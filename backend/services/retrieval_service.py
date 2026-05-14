import re
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from qdrant_client.http import models

from config.settings import settings
from config.clients import qdrant_client
from config.logger import logger
from embeddings import create_embeddings

# 1. Load heavy models once at startup
logger.info("Loading CrossEncoder Re-ranker into memory...")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

class RetrievalService:
    # 2. Class-level state (Replaces the dangerous 'global' variables)
    _chunks = None
    _bm25 = None

    def __init__(self):
        self.qdrant = qdrant_client

    # ==========================================
    # MEMORY MANAGEMENT
    # ==========================================
    @classmethod
    async def sync_memory_state(cls):
        """Stateless recovery: Pulls data from Qdrant if the server restarts."""
        logger.warning("RAM is empty! Recovering state directly from Qdrant database...")
        if not await qdrant_client.collection_exists(collection_name=settings.COLLECTION_NAME):
            return False
            
        records, _ = await qdrant_client.scroll(
            collection_name=settings.COLLECTION_NAME,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        sorted_records = sorted(records, key=lambda x: x.payload["original_index"])
        cls._chunks = [record.payload["text"] for record in sorted_records]
        
        tokenized = [chunk.split() for chunk in cls._chunks]
        cls._bm25 = BM25Okapi(tokenized)
        logger.info("Memory state successfully recovered.")
        return True

    @classmethod
    def update_index(cls, new_chunks):
        """Updates the memory cache instantly after a new file is uploaded."""
        cls._chunks = new_chunks
        tokenized = [chunk.split() for chunk in cls._chunks]
        cls._bm25 = BM25Okapi(tokenized)
        logger.info(f"Memory index updated with {len(new_chunks)} chunks.")

    # ==========================================
    # SEARCH PIPELINE
    # ==========================================
    async def execute_hybrid_search(self, original_query: str, enriched_query: str, expanded_queries: list):
        """Runs the entire hybrid retrieval and reranking pipeline."""
        
        # 1. Safety Check
        if self.__class__._chunks is None:
            success = await self.sync_memory_state()
            if not success:
                raise ValueError("Database is empty. Please upload a document.")

        chunks = self.__class__._chunks
        bm25 = self.__class__._bm25

        # 2. Vector Search (Qdrant)
        query_embedding = await create_embeddings([enriched_query.lower()])
        response = await self.qdrant.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=query_embedding[0].tolist(),
            limit=settings.TOP_K_RESULTS
        )
        vector_results = [hit.payload["original_index"] for hit in response.points]

        # 3. Keyword Search (BM25)
        bm25_results = []
        all_queries = expanded_queries + [original_query, enriched_query]
        for q in all_queries:
            scores = bm25.get_scores(q.lower().split())
            ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            bm25_results.extend(ranked[:3])
        bm25_results = list(dict.fromkeys(bm25_results)) # Remove duplicates

        # 4. Numeric Boost Search
        numeric_results = []
        numbers_in_query = re.findall(r'\d+', original_query)
        if numbers_in_query:
            for i, chunk in enumerate(chunks):
                if any(num in chunk for num in numbers_in_query):
                    numeric_results.append(i)
        numeric_results = numeric_results[:3]

        # 5. Hybrid Merge
        combined_indices = []
        max_len = max(len(vector_results + numeric_results), len(bm25_results))
        for i in range(max_len):
            if i < len(vector_results) and vector_results[i] not in combined_indices:
                combined_indices.append(vector_results[i])
            if i < len(bm25_results) and bm25_results[i] not in combined_indices:
                combined_indices.append(bm25_results[i])
            if len(combined_indices) >= settings.TOP_K_RESULTS * 2:
                break
                
        retrieved_chunks = [chunks[i] for i in combined_indices if i < len(chunks)]

        # 6. Cross-Encoder Re-Ranking
        if not retrieved_chunks:
            return []
            
        pairs = [[enriched_query, chunk] for chunk in retrieved_chunks]
        scores = reranker.predict(pairs)
        ranked_pairs = sorted(zip(scores, retrieved_chunks), reverse=True)
        
        return [chunk for score, chunk in ranked_pairs][:settings.TOP_K_RESULTS]