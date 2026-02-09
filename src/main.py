"""
Legal RAG API - FastAPI Entry Point.
Sistema de Recuperação Augmentada por Geração para documentos jurídicos.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.router import api_router
from core.health import full_health_check

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    # Startup
    logger.info("Iniciando Legal RAG API...")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"Ollama: {settings.OLLAMA_BASE_URL}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    logger.info(f"LLM Model: {settings.LLM_MODEL}")

    yield

    # Shutdown
    logger.info("Encerrando Legal RAG API...")


# Create FastAPI app
app = FastAPI(
    title="Legal RAG API",
    description="""
    API REST para sistema de Recuperação Augmentada por Geração (RAG) 
    especializado em documentos jurídicos brasileiros.

    ## Funcionalidades

    - **Indexação de Documentos**: Processa PDFs jurídicos e armazena embeddings no PostgreSQL
    - **Busca Semântica**: Pesquisa em código penal, constituição federal e outros documentos
    - **Modo Híbrido de Busca**: Busca em TODAS as coleções ou em collection específica
    - **Agente Jurídico**: Gera respostas fundamentadas com citação de fontes

    ## Models

    - Embeddings: BGE-M3 (Ollama)
    - LLM: Qwen 2.5 7b (Ollama)
    - Vector Store: PostgreSQL + pgvector
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": "Legal RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Verifica status do banco de dados e Ollama.
    """
    health_status = await full_health_check()
    return health_status


@app.get("/api/v1/info", tags=["Info"])
async def app_info():
    """Informações da aplicação."""
    return {
        "name": "Legal RAG API",
        "version": "1.0.0",
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.LLM_MODEL,
        "collections": settings.valid_collections,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
