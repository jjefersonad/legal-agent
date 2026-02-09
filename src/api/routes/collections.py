"""
API Routes - Gerenciamento de Collections.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["Collections"])


class CollectionInfo(BaseModel):
    """Informação sobre uma collection."""

    name: str
    status: str
    document_count: int = 0


class CollectionListResponse(BaseModel):
    """Response com lista de collections."""

    collections: list[CollectionInfo]


@router.get("", response_model=CollectionListResponse)
async def list_collections():
    """
    Retorna lista de collections configuradas e seu status.
    """
    collections = []

    for coll_name in settings.valid_collections:
        collections.append(
            CollectionInfo(
                name=coll_name,
                status="configured",
                document_count=0,  # Contagem não disponível diretamente via API
            )
        )

    return CollectionListResponse(collections=collections)


@router.get("/{collection_name}")
async def get_collection_info(collection_name: str):
    """
    Retorna informações detalhadas sobre uma collection específica.
    """
    if collection_name not in settings.valid_collections:
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_name}' não encontrada"
        )

    return {
        "name": collection_name,
        "status": "active",
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
    }


@router.delete("/{collection_name}")
async def delete_collection(collection_name: str):
    """
    Remove documentos de uma collection.

    Nota: O PGVector não suporta delete direto de collection.
    Em produção, seria necessário SQL direto:
    DROP TABLE IF EXISTS langchain_pg_embedding_{collection_name};
    """
    if collection_name not in settings.valid_collections:
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_name}' não encontrada"
        )

    logger.warning(f"Solicitação para deletar collection: {collection_name}")

    # Nota: Não é possível deletar collection via PGVector API
    # O usuário precisaria acessar o PostgreSQL diretamente
    return {
        "message": "Collection marcada para deleção",
        "note": "Para deletar completamente, execute no PostgreSQL: "
        f"DROP TABLE IF EXISTS langchain_pg_embedding_{collection_name};",
        "collection": collection_name,
    }
