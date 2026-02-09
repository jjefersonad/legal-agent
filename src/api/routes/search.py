"""
API Routes - Busca Semântica e Agente Jurídico.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from config import settings
from services.agent import JuridicalAgent, create_juridical_agent
from services.rag_service import create_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    """Request para busca semântica."""

    question: str = Field(..., description="Pergunta jurídica", min_length=3)
    top_k: Optional[int] = Field(
        default=5, ge=1, le=20, description="Resultados por collection"
    )


class SearchResponse(BaseModel):
    """Response da busca."""

    question: str
    answer: str
    sources: List[dict]
    search_mode: str
    collection_used: Optional[str] = None


class ContextSearchRequest(BaseModel):
    """Request para apenas recuperar contexto (sem gerar resposta)."""

    question: str = Field(..., description="Pergunta jurídica")
    collection: Optional[str] = Field(
        default=None, description="Collection específica (None = todas)"
    )
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class ContextSearchResponse(BaseModel):
    """Response com contexto recuperado (sem geração de resposta)."""

    question: str
    combined_context: str
    documents_count: int
    sources: List[dict]
    collections_searched: List[str]


@router.post("", response_model=SearchResponse)
async def search_all(request: SearchRequest):
    """
    Busca em TODAS as collections disponíveis.

    O agente pesquisa no Código Penal, Constituição Federal e
    quaisquer outras collections indexadas, retornando uma resposta
    fundamentada com citação de fontes.
    """
    logger.info(f"Busca em TODAS as collections: '{request.question[:50]}...'")

    try:
        agent = create_juridical_agent()

        result = agent.ask(
            question=request.question, search_mode="all", top_k=request.top_k
        )

        return SearchResponse(
            question=result.question,
            answer=result.answer,
            sources=result.sources,
            search_mode=result.search_mode,
            collection_used=result.collection_used,
        )

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar busca: {str(e)}"
        )


@router.post("/{collection_name}", response_model=SearchResponse)
async def search_collection(collection_name: str, request: SearchRequest):
    """
    Busca em uma collection específica.

    - **collection_name**: Nome da collection (ex: codigo_penal, constituicao_federal)
    - **question**: Pergunta jurídica
    - **top_k**: Número de resultados (default 5)
    """
    logger.info(f"Busca em '{collection_name}': '{request.question[:50]}...'")

    # Validar collection
    if collection_name not in settings.valid_collections:
        # Allow dynamic collections
        if not collection_name.replace("_", "").replace("-", "").isalnum():
            raise HTTPException(
                status_code=400, detail=f"Collection name inválido: {collection_name}"
            )

    try:
        agent = create_juridical_agent()

        result = agent.ask(
            question=request.question,
            search_mode="specific",
            collection=collection_name,
            top_k=request.top_k,
        )

        return SearchResponse(
            question=result.question,
            answer=result.answer,
            sources=result.sources,
            search_mode=result.search_mode,
            collection_used=result.collection_used,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar busca: {str(e)}"
        )


@router.get("/collections")
async def list_collections():
    """
    Retorna lista de collections válidas configuradas.
    """
    return {
        "collections": settings.valid_collections,
        "default_collection": settings.COLLECTION_PENAL,
    }


@router.post("/context", response_model=ContextSearchResponse)
async def get_context(request: ContextSearchRequest):
    """
    Apenas recupera contexto (não gera resposta com LLM).

    Útil para debugging ou quando o contexto será usado por outro sistema.
    """
    logger.info(f"Recuperando contexto: '{request.question[:50]}...'")

    try:
        rag_service = create_rag_service()

        # Determinar collections a buscar
        if request.collection:
            collections_to_search = [request.collection]
        else:
            collections_to_search = settings.valid_collections

        # Recuperar contexto
        context_result = rag_service.get_combined_context(request.question)

        return ContextSearchResponse(
            question=request.question,
            combined_context=context_result.combined_context,
            documents_count=len(context_result.documents),
            sources=context_result.sources_meta,
            collections_searched=collections_to_search,
        )

    except Exception as e:
        logger.error(f"Erro ao recuperar contexto: {e}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
