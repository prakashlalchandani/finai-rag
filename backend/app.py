import langchain
langchain.debug = True
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import shutil
import re
import uuid
import os

# --- New Database Imports ---
from config.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import models.model as models
# ----------------------------

from chunking import create_chunks
from embeddings import create_embeddings
from services.generation_service import GenerationService
from services.retrieval_service import RetrievalService
from vector_store import build_qdrant_index

from evaluation import check_retrieval
from config.settings import settings
from config.logger import logger

from pydantic import BaseModel, Field
from sqlalchemy import select
from config.auth import get_password_hash, verify_password, create_access_token

# Load environment variables
load_dotenv()

app = FastAPI(title="FinAudit AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "API is running"}

class UserRegister(BaseModel):
    username: str
    email: str
    password: str = Field(..., max_length=72)

class UserLogin(BaseModel):
    email: str
    password: str = Field(..., max_length=72)

# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/register")
async def register_user(user: UserRegister, db: AsyncSession = Depends(get_db)):
    logger.info(f"Registering new user: {user.email}")
    
    # Check if user already exists
    stmt = select(models.User).where(models.User.email == user.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password and save
    hashed_pw = get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        email=user.email, 
        hashed_password=hashed_pw
    )
    db.add(new_user)
    await db.commit()
    
    return {"message": "User created successfully! You can now log in."}

@app.post("/login")
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):
    logger.info(f"Login attempt for: {user.email}")
    
    # Fetch user from DB
    stmt = select(models.User).where(models.User.email == user.email)
    result = await db.execute(stmt)
    db_user = result.scalars().first()

    # Verify Email & Password
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate JWT Token (Saving user_id inside the token)
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": db_user.id,
        "username": db_user.username
    }

# -----------------------------
# Upload and index Document
# -----------------------------
@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form("default_user"),
    db: AsyncSession = Depends(get_db) # <-- DB Session Injected!
):
    logger.info(f"📥 [UPLOAD START] Receiving file: {file.filename}")
    
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        os.makedirs("sample_data", exist_ok=True)
        file_location = f"sample_data/{unique_filename}"

        # 1. Saving File
        logger.info(f"💾 Saving file locally to {file_location}...")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info("✅ File saved successfully.")

        # 2. Chunking
        logger.info("🔪 [CHUNKING START] Initiating text extraction and chunking...")
        chunks = await create_chunks(file_location)
        logger.info(f"✅ [CHUNKING SUCCESS] Created {len(chunks)} chunks.")

        # 3. Embeddings
        logger.info("🧠 [EMBEDDING START] Sending chunks to Google Gemini API...")
        embeddings = await create_embeddings(chunks)
        logger.info("✅ [EMBEDDING SUCCESS] Embeddings generated successfully.")

        # 4. Vector Store
        logger.info("🗄️ [DATABASE START] Indexing vectors into Qdrant for {session_id}...")
        await build_qdrant_index(embeddings, chunks, file.filename, session_id)
        logger.info("✅ [DATABASE SUCCESS] Qdrant index built successfully.")
        
        # 5. Local Memory
        logger.info("🔄 Updating local memory (BM25 & Chunks) for {session_id}...")
        RetrievalService.update_index(session_id, file.filename, chunks)
        logger.info("✅ Local memory updated.")

        # =============== POSTGRESQL LAYER =================
        logger.info("💾 Saving document metadata to PostgreSQL...")
        db_doc = models.Document(
            user_id=int(session_id) if session_id.isdigit() else 1,  # FIXED: Assign actual user ID
            filename=file.filename,
            unique_filename=unique_filename,
            status="indexed"
        )
        db.add(db_doc)
        await db.commit()
        # ==================================================

        logger.info("🎉 [UPLOAD PIPELINE COMPLETE] Document is ready for queries.")
        return {
            "message": "Document uploaded and indexed successfully",
            "chunks_created": len(chunks),
        }
        
    except Exception as e:
        await db.rollback() # Agar fail hua to DB changes rollback karo
        logger.error(f"❌ [UPLOAD FAILED] An error occurred during upload pipeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# -----------------------------
# Search endpoint
# -----------------------------
@app.get("/search")
async def search_query(
    query: str,
    document_selector: str = "all", # <-- NAYA PARAMETER
    session_id: str = "default_user",
    gen_service: GenerationService = Depends(),
    retrieval_service: RetrievalService = Depends(),
    db: AsyncSession = Depends(get_db) # <-- DB Session Injected!
):
    logger.info(f"🔍 [QUERY START] Received query: '{query}' for session: {session_id}")
    
    try:
        # PHASE 1: ROUTING
        logger.info("🚦 Routing query...")
        routing_decision = await gen_service.route_query(query)
        
        if routing_decision["route"] == "chat":
            logger.info("💬 Route decided: CHAT (Bypassing RAG)")
            
            # Save Chat to DB
            await gen_service.save_message_to_db(db, session_id, "user", query)
            await gen_service.save_message_to_db(db, session_id, "ai", routing_decision["chat_response"])
            
            return {
                "query": query,
                "answer": routing_decision["chat_response"],
                "sources_used": [],
                "routed_via": "Fast Chat Agent"
            }

        logger.info("📚 Route decided: RAG (Initiating retrieval pipeline)")

        # PHASE 2: TRANSLATION & EXPANSION
        logger.info("🔄 Expanding query with synonyms and variations...")
        legal_synonyms = await gen_service.expand_query_with_synonyms(query)
        enriched_search_query = f"{query} {legal_synonyms}"
        expanded_queries = await gen_service.generate_multi_queries(query) 
        logger.info(f"✅ Query expanded. Synonyms: {legal_synonyms}")

        # PHASE 3: HYBRID RETRIEVAL
        logger.info("🔎 Executing Hybrid Search (Vector + BM25 + Cross-Encoder)...")
        try:
            best_chunks = await retrieval_service.execute_hybrid_search(
                original_query=query,
                enriched_query=enriched_search_query,
                expanded_queries=expanded_queries,
                session_id=session_id, # <-- Yahan session_id add kiya
                document_selector=document_selector # <-- NAYA ARGUMENT
            )
            logger.info(f"✅ Hybrid Search complete. Found {len(best_chunks)} highly relevant chunks.")
        except ValueError as e:
            logger.warning(f"⚠️ Search aborted: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        # PHASE 4: SYNTHESIS
        logger.info("✍️ Generating final answer with LLM...")
        # Passing 'db' to gen_service for saving history
        final_answer = await gen_service.generate_answer(query, best_chunks, session_id, db)
        logger.info("🎉 [QUERY COMPLETE] Answer generated successfully.")
        
        return {
            "query": query,
            "answer": final_answer,
            "sources_used": best_chunks,
            "synonyms_generated": legal_synonyms
        }
        
    except Exception as e:
        logger.error(f"❌ [QUERY FAILED] An error occurred during search pipeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search pipeline failed: {str(e)}")

# -----------------------------
# Fetch User Documents Endpoint
# -----------------------------
@app.get("/documents")
async def get_user_documents(
    session_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = int(session_id) if session_id.isdigit() else 1
        # Fetch distinct filenames for this specific user
        stmt = select(models.Document.filename).where(models.Document.user_id == user_id).distinct()
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        return {"documents": documents}
    except Exception as e:
        logger.error(f"❌ Failed to fetch documents: {e}")
        return {"documents": []}

from qdrant_client.http import models as qmodels
from config.clients import qdrant_client

# -----------------------------
# Delete Document Endpoint
# -----------------------------
@app.delete("/documents/{filename}")
async def delete_document(
    filename: str,
    session_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"🗑️ [DELETE START] Request to delete {filename} for session {session_id}")
    try:
        user_id = int(session_id) if session_id.isdigit() else 1
        
        # 1. Delete from PostgreSQL Database
        stmt = select(models.Document).where(
            models.Document.user_id == user_id, 
            models.Document.filename == filename
        )
        result = await db.execute(stmt)
        doc_to_delete = result.scalars().first()

        if doc_to_delete:
            await db.delete(doc_to_delete)
            await db.commit()
            logger.info("✅ Removed from PostgreSQL.")

        # 2. Delete Vectors from Qdrant
        await qdrant_client.delete(
            collection_name=settings.COLLECTION_NAME,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(key="session_id", match=qmodels.MatchValue(value=session_id)),
                        qmodels.FieldCondition(key="document_name", match=qmodels.MatchValue(value=filename))
                    ]
                )
            )
        )
        logger.info("✅ Vectors removed from Qdrant.")

        # 3. Clear from Local RAM (BM25 Cache)
        if session_id in RetrievalService._chunks and filename in RetrievalService._chunks[session_id]:
            del RetrievalService._chunks[session_id][filename]
            if filename in RetrievalService._bm25[session_id]:
                del RetrievalService._bm25[session_id][filename]
            logger.info("✅ Removed from local memory cache.")

        return {"message": f"Successfully deleted {filename}"}
        
    except Exception as e:
        logger.error(f"❌ [DELETE FAILED]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete document from server.")

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
async def evaluate_system(
    gen_service: GenerationService = Depends(),
    retrieval_service: RetrievalService = Depends()
):
    if retrieval_service.__class__._chunks is None:
        success = await retrieval_service.sync_memory_state()
        if not success:
            raise HTTPException(status_code=400, detail="Database is empty. Upload a Document first.")
            
    chunks = retrieval_service.__class__._chunks
    expected_answers = extract_expected_values(chunks)

    correct = 0
    total = len(expected_answers)
    results_summary = []

    for query, expected_answer in expected_answers.items():
        legal_synonyms = await gen_service.expand_query_with_synonyms(query)
        enriched_search_query = f"{query} {legal_synonyms}"
        expanded_queries = await gen_service.generate_multi_queries(query)

        retrieved_chunks = await retrieval_service.execute_hybrid_search(
            original_query=query,
            enriched_query=enriched_search_query,
            expanded_queries=expanded_queries
        )

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