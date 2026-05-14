from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams, PointStruct
from config.settings import settings # <-- FIXED: Imported the lowercase instance
from config.clients import qdrant_client as client
import uuid

async def build_qdrant_index(embeddings, chunks, filename):
    dimension = len(embeddings[0])

    # 1. Housekeeping: Delete the old collection if it exists
    if await client.collection_exists(collection_name=settings.COLLECTION_NAME):
        await client.delete_collection(collection_name=settings.COLLECTION_NAME)

    print(f"Creating collection: {settings.COLLECTION_NAME}")
    
    # 2. Create the clean collection
    await client.create_collection(
        collection_name=settings.COLLECTION_NAME,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )

    # 3. Insert points
    points = []
    for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload={"text": chunk, "original_index": i, "document_name": filename}
        ))

    await client.upsert(
        collection_name=settings.COLLECTION_NAME,
        points=points
    )
    return True


async def search_qdrant(query_embedding, target_document=None):
    if not await client.collection_exists(collection_name=settings.COLLECTION_NAME):
        return []

    search_filter = None
    if target_document:
        search_filter = models.Filter(
            must=[models.FieldCondition(key="document_name", match=models.MatchValue(value=target_document))]
        )

    # 1. First, await the entire response from Qdrant
    response = await client.query_points(
        collection_name=settings.COLLECTION_NAME, 
        query=query_embedding.tolist(),
        query_filter=search_filter, 
        limit=settings.TOP_K_RESULTS 
    )
    
    # 2. Then, extract the points and return the original index!
    return [hit.payload["original_index"] for hit in response.points]


async def get_all_chunks():
    """Extracts all text chunks directly from the Qdrant database payloads."""
    # <-- ADD AWAIT
    if not await client.collection_exists(collection_name=settings.COLLECTION_NAME):
        return []
        
    # <-- ADD AWAIT
    records, _ = await client.scroll(
        collection_name=settings.COLLECTION_NAME,
        limit=10000,
        with_payload=True,
        with_vectors=False
    )
    
    sorted_records = sorted(records, key=lambda x: x.payload["original_index"])
    return [record.payload["text"] for record in sorted_records]