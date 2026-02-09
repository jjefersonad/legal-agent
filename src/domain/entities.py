"""
Entidades do domínio Legal RAG API.
Pydantic models para validação de dados e API responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class CollectionName(str, Enum):
    """Enum para nomes de collections disponíveis."""

    CODIGO_PENAL = "codigo_penal"
    CONSTITUICAO_FEDERAL = "constituicao_federal"


class IndexDocumentRequest(BaseModel):
    """Request para indexação de documento."""

    file_path: str = Field(..., description="Caminho do arquivo PDF a ser indexado")
    collection_name: str = Field(..., description="Nome da collection")


class IndexDocumentResponse(BaseModel):
    """Response da indexação de documento."""

    status: str
    collection: str
    chunks_created: int
    embeddings_generated: int
    processing_time_seconds: float


class SearchRequest(BaseModel):
    """Request para busca semântica."""

    question: str = Field(..., description="Pergunta jurídica a ser pesquisada")
    top_k: Optional[int] = Field(
        default=5, ge=1, le=20, description="Número de resultados"
    )


class SearchResponse(BaseModel):
    """Response da busca semântica."""

    question: str
    answer: str
    sources: List["SourceDocument"]
    search_mode: str
    collection_used: Optional[str] = None


class SourceDocument(BaseModel):
    """Documento fonte recuperado."""

    content: str
    page: Optional[int] = None
    score: Optional[float] = None
    collection: str


class CollectionInfo(BaseModel):
    """Informação sobre uma collection."""

    name: str
    document_count: int
    status: str


class CollectionListResponse(BaseModel):
    """Response com lista de collections."""

    collections: List[CollectionInfo]


class HealthResponse(BaseModel):
    """Response do health check."""

    status: str
    database: str
    ollama: str
    version: str


class ErrorResponse(BaseModel):
    """Response de erro."""

    error: str
    detail: Optional[str] = None
    status_code: int


# Atualizar model de SearchResponse para referência circular
SearchResponse.model_rebuild()
