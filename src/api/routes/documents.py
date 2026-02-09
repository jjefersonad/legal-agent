"""
API Routes - Indexação de Documentos.
"""

import os
import tempfile
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional

from config import settings
from services.indexer import IndexerService, create_indexer_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


class IndexRequest(BaseModel):
    """Request para indexar documento por caminho."""

    file_path: str = Field(..., description="Caminho do arquivo PDF")
    collection_name: str = Field(..., description="Nome da collection de destino")
    pre_delete_collection: bool = Field(
        default=False, description="Se True, deleta collection existente"
    )


class UploadResponse(BaseModel):
    """Response do upload."""

    status: str
    collection: str
    chunks_created: int
    embeddings_generated: int
    processing_time_seconds: float
    message: str
    saved_path: Optional[str] = None


class IndexResponse(BaseModel):
    """Response da indexação."""

    status: str
    collection: str
    chunks_created: int
    embeddings_generated: int
    processing_time_seconds: float
    message: str


@router.post("/{collection_name}", response_model=IndexResponse)
async def index_document(collection_name: str, request: IndexRequest):
    """
    Indexa um documento PDF na collection especificada.

    - **collection_name**: Nome da collection (validation against valid collections)
    - **file_path**: Caminho do arquivo PDF
    - **pre_delete_collection**: Se True, apaga collection existente antes de indexar
    """
    logger.info(f"Request para indexar: {request.file_path} → {collection_name}")

    # Validar collection name
    if collection_name not in settings.valid_collections:
        # Allow custom collections too
        if not collection_name.replace("_", "").replace("-", "").isalnum():
            raise HTTPException(
                status_code=400, detail=f"Collection name inválido: {collection_name}"
            )

    try:
        indexer = create_indexer_service()

        # Override collection do request se vier diferente
        effective_collection = request.collection_name or collection_name

        result = indexer.index_document(
            file_path=request.file_path,
            collection_name=effective_collection,
            pre_delete_collection=request.pre_delete_collection,
        )

        return IndexResponse(
            status=result.status,
            collection=result.collection,
            chunks_created=result.chunks_created,
            embeddings_generated=result.embeddings_generated,
            processing_time_seconds=result.processing_time,
            message=f"Documento indexado com sucesso em '{result.collection}'",
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao indexar documento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/{collection_name}/async")
async def index_document_async(
    collection_name: str, request: IndexRequest, background_tasks: BackgroundTasks
):
    """
    Indexa documento de forma assíncrona (para arquivos grandes).

    O processamento ocorre em background e não bloqueia a resposta.
    """
    logger.info(f"Request assíncrono para indexar: {request.file_path}")

    def process_index():
        """Processa indexação em background."""
        try:
            indexer = create_indexer_service()
            indexer.index_document(
                file_path=request.file_path,
                collection_name=collection_name,
                pre_delete_collection=request.pre_delete_collection,
            )
        except Exception as e:
            logger.error(f"Erro em indexação background: {e}")

    background_tasks.add_task(process_index)

    return {
        "status": "accepted",
        "message": f"Indexação iniciada em background para '{collection_name}'",
        "file_path": request.file_path,
    }


@router.get("/{collection_name}/status")
async def get_index_status(collection_name: str):
    """
    Retorna status da collection (número de documentos, etc).
    """
    from pipelines.rag.retriever import create_rag_retriever

    try:
        retriever = create_rag_retriever(collection_name)
        # Nota: PGVector não expõe count diretamente,
        # retorna status básico
        return {
            "collection": collection_name,
            "status": "exists",
            "note": "Contagem não disponível diretamente via API",
        }
    except Exception as e:
        return {"collection": collection_name, "status": "error", "detail": str(e)}


# ========================
# UPLOAD DE ARQUIVOS
# ========================

DATA_DIR = "data"


@router.post("/{collection_name}/upload", response_model=UploadResponse)
async def upload_and_index_document(
    collection_name: str,
    file: UploadFile = File(...),
    pre_delete_collection: bool = False,
):
    """
    Faz upload de um arquivo PDF e indexa diretamente.

    - **collection_name**: Nome da collection de destino
    - **file**: Arquivo PDF para upload
    - **pre_delete_collection**: Se True, deleta collection existente antes de indexar
    """
    # Validar collection name
    if not collection_name.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(
            status_code=400, detail=f"Collection name inválido: {collection_name}"
        )

    # Validar extensão do arquivo
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Apenas arquivos PDF são suportados"
        )

    # Criar diretório de destino se não existir
    os.makedirs(DATA_DIR, exist_ok=True)

    # Gerar nome de arquivo único para evitar conflitos
    import uuid

    safe_filename = f"{collection_name}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(DATA_DIR, safe_filename)

    try:
        # Salvar arquivo enviado
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Arquivo salvo: {file_path}")

        # Indexar documento
        indexer = create_indexer_service()
        result = indexer.index_document(
            file_path=file_path,
            collection_name=collection_name,
            pre_delete_collection=pre_delete_collection,
        )

        return UploadResponse(
            status=result.status,
            collection=result.collection,
            chunks_created=result.chunks_created,
            embeddings_generated=result.embeddings_generated,
            processing_time_seconds=result.processing_time,
            message=f"Arquivo '{file.filename}' indexado com sucesso em '{collection_name}'",
            saved_path=file_path,
        )

    except Exception as e:
        # Limpar arquivo em caso de erro
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Erro ao processar upload: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar arquivo: {str(e)}"
        )
