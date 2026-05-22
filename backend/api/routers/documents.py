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

# Naye folder structure ke hisaab se imports update kiye hain
from services.chunking import create_chunks
from services.embeddings import create_embeddings
from services.vector_store import build_qdrant_index
from services.retrieval_service import RetrievalService

router = APIRouter()

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form("default_user"),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"📥 [UPLOAD START] Receiving file: {file.filename}")
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

        user_id_str = str(session_id).split('_')[0]
        actual_user_id = int(user_id_str) if user_id_str.isdigit() else 1

        db_doc = models.Document(
            user_id=actual_user_id,
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
async def get_user_documents(session_id: str = "default_user", db: AsyncSession = Depends(get_db)):
    try:
        user_id_str = str(session_id).split('_')[0]
        user_id = int(user_id_str) if user_id_str.isdigit() else 1
        stmt = select(models.Document.filename).where(models.Document.user_id == user_id).distinct()
        result = await db.execute(stmt)
        return {"documents": result.scalars().all()}
    except Exception as e:
        logger.error(f"❌ Failed to fetch documents: {e}")
        return {"documents": []}

@router.delete("/documents/{filename}")
async def delete_document(filename: str, session_id: str = "default_user", db: AsyncSession = Depends(get_db)):
    try:
        user_id_str = str(session_id).split('_')[0]
        user_id = int(user_id_str) if user_id_str.isdigit() else 1
        
        stmt = select(models.Document).where(models.Document.user_id == user_id, models.Document.filename == filename)
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