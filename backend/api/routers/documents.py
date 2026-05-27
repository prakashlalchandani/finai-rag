from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import shutil
import uuid

from config.database import get_db
import models.model as models
from config.logger import logger
from config.settings import settings
from config.clients import qdrant_client
from qdrant_client.http import models as qmodels
from config.auth import get_current_user

# Naye folder structure ke hisaab se imports update kiye hain
from services.chunking import create_chunks
from services.embeddings import create_embeddings
from services.vector_store import build_qdrant_index
from services.retrieval_service import RetrievalService

router = APIRouter()

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"📥 [UPLOAD START] Receiving file: {file.filename}")
    if not session_id.startswith(f"{current_user.id}_"):
        raise HTTPException(status_code=403, detail="Invalid session_id for current user")
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        os.makedirs("sample_data", exist_ok=True)
        file_location = f"sample_data/{unique_filename}"

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks = await create_chunks(file_location)
        embeddings = await create_embeddings(chunks)
        await build_qdrant_index(embeddings, chunks, file.filename, session_id)
        
        RetrievalService.update_index(session_id, file.filename, chunks)

        db_doc = models.Document(
            user_id=current_user.id,
            filename=file.filename,
            unique_filename=unique_filename,
            status="indexed"
        )
        db.add(db_doc)
        await db.commit()

        return {"message": "Document uploaded and indexed successfully", "chunks_created": len(chunks)}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ [UPLOAD FAILED]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents")
async def get_user_documents(
    session_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        if not session_id.startswith(f"{current_user.id}_"):
            raise HTTPException(status_code=403, detail="Invalid session_id for current user")

        stmt = select(models.Document.filename).where(models.Document.user_id == current_user.id).distinct()
        result = await db.execute(stmt)
        return {"documents": result.scalars().all()}
    except Exception as e:
        logger.error(f"❌ Failed to fetch documents: {e}")
        return {"documents": []}

@router.delete("/documents/{filename}")
async def delete_document(
    filename: str, 
    session_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        if not session_id.startswith(f"{current_user.id}_"):
            raise HTTPException(status_code=403, detail="Invalid session_id for current user")
        
        stmt = select(models.Document).where(models.Document.user_id == current_user.id, models.Document.filename == filename)
        result = await db.execute(stmt)
        doc_to_delete = result.scalars().first()

        if doc_to_delete:
            await db.delete(doc_to_delete)
            await db.commit()

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

        if session_id in RetrievalService._chunks and filename in RetrievalService._chunks[session_id]:
            del RetrievalService._chunks[session_id][filename]
            if filename in RetrievalService._bm25[session_id]:
                del RetrievalService._bm25[session_id][filename]

        return {"message": f"Successfully deleted {filename}"}
        
    except Exception as e:
        logger.error(f"❌ [DELETE FAILED]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete document.")

@router.delete("/cleanup")
async def cleanup_user_data(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Deletes all documents, vectors, and physical files for the current user upon logout/session end."""
    logger.info(f"🧹 [CLEANUP INITIATED] Wiping data for user: {current_user.id}")
    
    try:
        # Step 1: SQL Database se user ke saare documents fetch karo
        stmt = select(models.Document).where(models.Document.user_id == current_user.id)
        result = await db.execute(stmt)
        user_docs = result.scalars().all()

        for doc in user_docs:
            # Step 2: Hard Drive se physical file delete karo
            file_path = f"sample_data/{doc.unique_filename}"
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Deleted file: {file_path}")

            # Step 3: SQL Database se record delete karo (Cascade delete will handle it if mapped correctly, but doing it explicitly here)
            await db.delete(doc)

        await db.commit()

        # Step 4: Qdrant Vector Database se saare vectors delete karo jinme yeh session_id ho
        await qdrant_client.delete(
            collection_name=settings.COLLECTION_NAME,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(key="session_id", match=qmodels.MatchValue(value=session_id)),
                    ]
                )
            )
        )
        logger.info(f"🗑️ Deleted all Qdrant vectors for session: {session_id}")

        # Step 5: Local Memory Variables (BM25/Chunks) se data clear karo
        if session_id in RetrievalService._chunks:
            del RetrievalService._chunks[session_id]
        if session_id in RetrievalService._bm25:
            del RetrievalService._bm25[session_id]

        return {"message": "All user data cleaned up successfully."}

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ [CLEANUP FAILED]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cleanup user data.")