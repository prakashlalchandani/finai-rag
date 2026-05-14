import langchain
langchain.debug = True
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import shutil
import re
import uuid
import os

from chunking import create_chunks
from query_transform import generate_hyde_document, generate_multi_queries
from embeddings import create_embeddings
from services.generation_service import GenerationService
from services.retrieval_service import RetrievalService
from vector_store import build_qdrant_index

from evaluation import check_retrieval
from config.settings import settings
from config.logger import logger

# Load environment variables
load_dotenv()

app = FastAPI(title="FinAudit AI Backend")

app.add_middleware(
    CORSMiddleware,
    # Pulling frontend URL from your settings file is a great practice!
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Global pipeline state 
chunks = None
bm25 = None

@app.get("/")
def health():
    return {"status": "API is running"}

# -----------------------------
# Upload and index Document
# -----------------------------
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Ensure directory exists
    os.makedirs("sample_data", exist_ok=True)
    file_location = f"sample_data/{unique_filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # AWAIT all heavy/network functions!
    chunks = await create_chunks(file_location)
    embeddings = await create_embeddings(chunks)
    await build_qdrant_index(embeddings, chunks, file.filename)
    
    # Local CPU math, no await needed
    RetrievalService.update_index(chunks)

    return {
        "message": "Document uploaded and indexed successfully",
        "chunks_created": len(chunks),
    }

# -----------------------------
# Search endpoint
# -----------------------------
from fastapi import HTTPException # Make sure this is imported at the top!

@app.get("/search")
async def search_query(
    query: str, 
    session_id: str = "default_user",
    gen_service: GenerationService = Depends(),
    retrieval_service: RetrievalService = Depends()
):
    # ==========================================
    # PHASE 1: ROUTING
    # ==========================================
    routing_decision = await gen_service.route_query(query)
    
    if routing_decision["route"] == "chat":
        return {
            "query": query,
            "answer": routing_decision["chat_response"],
            "sources_used": [],
            "routed_via": "Fast Chat Agent"
        }

    # ==========================================
    # PHASE 2: TRANSLATION & EXPANSION
    # ==========================================
    legal_synonyms = await gen_service.expand_query_with_synonyms(query)
    enriched_search_query = f"{query} {legal_synonyms}"
    
    # We are still pulling this from query_transform.py for now
    expanded_queries = await generate_multi_queries(query) 

    # ==========================================
    # PHASE 3: HYBRID RETRIEVAL
    # ==========================================
    try:
        best_chunks = await retrieval_service.execute_hybrid_search(
            original_query=query,
            enriched_query=enriched_search_query,
            expanded_queries=expanded_queries
        )
    except ValueError as e:
        # If the database is empty, we safely abort and tell the user
        raise HTTPException(status_code=400, detail=str(e))

    # ==========================================
    # PHASE 4: SYNTHESIS
    # ==========================================
    final_answer = await gen_service.generate_answer(query, best_chunks, session_id)
    
    return {
        "query": query,
        "answer": final_answer,
        "sources_used": best_chunks,
        "synonyms_generated": legal_synonyms
    }

# -----------------------------
# Dynamic expected-value extractor
# -----------------------------
def extract_expected_values(chunks):
    expected = {}
    patterns = {
        "What is EMI amount?": r"EMI.*?(\d[\d,]*)",
        "What is interest rate?": r"Interest.*?(\d+\.?\d*)",
        "Loan amount sanctioned?": r"Loan\s*Amount.*?(\d[\d,]*)",
        "Number of installments?": r"Installments?.*?(\d+)",
    }
    for question, pattern in patterns.items():
        for chunk in chunks:
            match = re.search(pattern, chunk, re.IGNORECASE)
            if match:
                expected[question] = match.group(1)
                break
    return expected

# -----------------------------
# Evaluation endpoint
# -----------------------------
@app.get("/evaluate")
async def evaluate_system():
    global chunks, bm25

    # --- THE STATELESS RECOVERY TRIGGER ---
    if chunks is None:
        chunks = await get_all_chunks()
        if not chunks:
            return {"error": "Upload a Document first."}
        bm25 = build_bm25(chunks)
    # --------------------------------------

    expected_answers = extract_expected_values(chunks)

    correct = 0
    total = len(expected_answers)
    results_summary = []

    for query, expected_answer in expected_answers.items():
        query_embedding = await create_embeddings([query.lower()])

        vector_results = await search_qdrant(query_embedding[0])
        bm25_results = bm25_search(bm25, query.lower(), chunks)
        numeric_results = numeric_boost_search(query, chunks)

        final_results = hybrid_search(vector_results + numeric_results, bm25_results)

        retrieved_chunks = [chunks[i] for i in final_results if i < len(chunks)]
        match = check_retrieval(expected_answer, retrieved_chunks)

        results_summary.append({
            "query": query,
            "expected": expected_answer,
            "match_found": match,
        })

        if match:
            correct += 1

    accuracy = correct / total if total else 0

    return {
        "accuracy": accuracy,
        "details": results_summary,
    }