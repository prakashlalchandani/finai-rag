from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams, PointStruct
from config.settings import settings 
from config.clients import qdrant_client as client
import uuid

async def build_qdrant_index(embeddings, chunks, filename, session_id: str):
    dimension = len(embeddings[0])

    # 1. Create collection if it doesn't exist
    if not await client.collection_exists(collection_name=settings.COLLECTION_NAME):
        print(f"Creating collection: {settings.COLLECTION_NAME}")
        await client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )

    # 2. FIX: Ensure the payload index for session_id always exists
    try:
        # Keep your existing session_id index
        await client.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="session_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        # ADD THIS NEW BLOCK for document_name
        await client.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="document_name",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        print("✅ Payload indices for 'session_id' and 'document_name' verified/created.")
    except Exception as e:
        print(f"Payload index status: {e}")

    # 3. Insert points with session_id tag
    points = []
    for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload={
                "text": chunk, 
                "original_index": i, 
                "document_name": filename,
                "session_id": session_id
            }
        ))

    await client.upsert(
        collection_name=settings.COLLECTION_NAME,
        points=points
    )

async def search_qdrant(query_embedding, session_id: str): # <-- Parameter added
    if not await client.collection_exists(collection_name=settings.COLLECTION_NAME):
        return []

    # 1. FIXED: Filter by session_id strictly!
    search_filter = models.Filter(
        must=[models.FieldCondition(key="session_id", match=models.MatchValue(value=session_id))]
    )

    # 2. Query Qdrant with the filter
    response = await client.query_points(
        collection_name=settings.COLLECTION_NAME, 
        query=query_embedding.tolist(),
        query_filter=search_filter, 
        limit=settings.TOP_K_RESULTS 
    )
    
    return [hit.payload["original_index"] for hit in response.points]


async def get_all_chunks(session_id: str): # <-- Parameter added
    """Extracts all text chunks directly from the Qdrant database for a specific session."""
    if not await client.collection_exists(collection_name=settings.COLLECTION_NAME):
        return []
        
    # 1. Scroll only the chunks that belong to this session
    records, _ = await client.scroll(
        collection_name=settings.COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="session_id", match=models.MatchValue(value=session_id))]
        ),
        limit=10000,
        with_payload=True,
        with_vectors=False
    )
    
    sorted_records = sorted(records, key=lambda x: x.payload["original_index"])
    return [record.payload["text"] for record in sorted_records]