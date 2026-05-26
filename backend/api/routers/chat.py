from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from config.logger import logger
from services.generation_service import GenerationService
from services.retrieval_service import RetrievalService
import models.model as models
from config.auth import get_current_user

router = APIRouter()

@router.get("/search")
async def search_query(
    query: str,
    document_selector: str = "all",
    session_id: str = "default_user",
    gen_service: GenerationService = Depends(),
    retrieval_service: RetrievalService = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not session_id.startswith(f"{current_user.id}_"):
        raise HTTPException(status_code=403, detail="Invalid session_id for current user")
    
    logger.info(f"🔍 [QUERY START] Received query: '{query}' for session: {session_id}")
    
    try:
        # PHASE 1: ROUTING
        routing_decision = await gen_service.route_query(query)
        
        if routing_decision["route"] == "chat":
            await gen_service.save_message_to_db(db, session_id, "user", query)
            await gen_service.save_message_to_db(db, session_id, "ai", routing_decision["chat_response"])
            return {
                "query": query, "answer": routing_decision["chat_response"],
                "sources_used": [], "routed_via": "Fast Chat Agent"
            }

        # PHASE 2: EXPANSION
        legal_synonyms = await gen_service.expand_query_with_synonyms(query)
        enriched_search_query = f"{query} {legal_synonyms}"
        expanded_queries = await gen_service.generate_multi_queries(query) 

        # PHASE 3: RETRIEVAL
        try:
            best_chunks = await retrieval_service.execute_hybrid_search(
                original_query=query, enriched_query=enriched_search_query,
                expanded_queries=expanded_queries, session_id=session_id, document_selector=document_selector
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # PHASE 4: SYNTHESIS
        final_answer = await gen_service.generate_answer(query, best_chunks, session_id, db)
        
        return {
            "query": query, "answer": final_answer,
            "sources_used": best_chunks, "synonyms_generated": legal_synonyms
        }
        
    except Exception as e:
        logger.error(f"❌ [QUERY FAILED]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search pipeline failed: {str(e)}")