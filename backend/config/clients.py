# config/clients.py
from groq import AsyncGroq
from qdrant_client import AsyncQdrantClient
from config.settings import settings

# 1. The Single Groq Client
# Used for fast, raw API calls (Routing, Query Expansion, Table Summarization)
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

# 2. The Single Qdrant Database Client
# Used for all vector database operations
qdrant_client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)