import asyncio
import os
from chunking import create_chunks
from embeddings import create_embeddings
from vector_store import build_qdrant_index
from services.generation_service import GenerationService
from services.retrieval_service import RetrievalService
from config.logger import logger

async def run_cli_pipeline(pdf_path: str):
    # 1. Initialize Services
    gen_service = GenerationService()
    ret_service = RetrievalService()

    # 2. Process and Index (The Upload Phase)
    logger.info(f"Processing document: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found.")
        return

    chunks = await create_chunks(pdf_path)
    embeddings = await create_embeddings(chunks)
    
    # Index to Qdrant
    filename = os.path.basename(pdf_path)
    await build_qdrant_index(embeddings, chunks, filename)
    
    # Update the service's memory state immediately
    ret_service.update_index(chunks)

    print("\n--- Document Indexed Successfully ---")

    # 3. Interactive Search Loop
    while True:
        query = input("\nAsk a question about the document (or type 'exit' to quit): ")
        if query.lower() in ['exit', 'quit']:
            break

        print("🔍 Searching and generating answer...")

        # A. Routing & Translation
        routing_decision = await gen_service.route_query(query)
        if routing_decision["route"] == "chat":
            print(f"\nAI (Chat): {routing_decision['chat_response']}")
            continue

        legal_synonyms = await gen_service.expand_query_with_synonyms(query)
        enriched_query = f"{query} {legal_synonyms}"
        multi_queries = await gen_service.generate_multi_queries(query)

        # B. Hybrid Retrieval & Reranking
        try:
            best_chunks = await ret_service.execute_hybrid_search(
                original_query=query,
                enriched_query=enriched_query,
                expanded_queries=multi_queries
            )
        except Exception as e:
            print(f"Retrieval Error: {e}")
            continue

        # C. Synthesis
        final_answer = await gen_service.generate_answer(query, best_chunks, "cli_session")

        print(f"\nAI (RAG): {final_answer}")
        print("-" * 30)
        print(f"Sources Used: {len(best_chunks)} chunks.")

if __name__ == "__main__":
    path = input("Enter PDF path: ").strip()
    # Remove quotes if the user copied path as "C:\path\to\file.pdf"
    path = path.replace('"', '').replace("'", "")
    asyncio.run(run_cli_pipeline(path))