"""
Configurações centralizadas da aplicação Legal RAG API.
Utiliza Pydantic Settings para carregamento de variáveis de ambiente.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ============================================
    # Banco de Dados PostgreSQL + pgvector
    # ============================================
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "juridico_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:password@localhost:5432/juridico_db"
    )

    # ============================================
    # Ollama Configuration
    # ============================================
    # Embedding usa porta 11434 (único container com bge-m3)
    OLLAMA_BASE_URL_EMBEDDING: str = "http://localhost:11434"
    # LLM pode usar porta 12434 (GPU mais rápida) ou 11434
    OLLAMA_BASE_URL_LLM: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "bge-m3:latest"
    LLM_MODEL: str = "glm-4.7:cloud"

    @property
    def OLLAMA_BASE_URL(self) -> str:
        """URL padrão do Ollama (mantido para compatibilidade)."""
        return self.OLLAMA_BASE_URL_EMBEDDING

    # ============================================
    # Collection Names
    # ============================================
    COLLECTION_PENAL: str = "codigo_penal"
    COLLECTION_CONSTITUCIONAL: str = "constituicao_federal"

    # ============================================
    # Chunk Configuration
    # ============================================
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # ============================================
    # RAG Configuration
    # ============================================
    TOP_K_RESULTS: int = 5
    LLM_TEMPERATURE: float = 0.1

    # ============================================
    # API Configuration
    # ============================================
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # ============================================
    # Embedding Configuration
    # ============================================
    EMBEDDING_DIMENSION: int = 1024

    @property
    def valid_collections(self) -> list[str]:
        """Retorna lista de collections válidas."""
        return [self.COLLECTION_PENAL, self.COLLECTION_CONSTITUCIONAL]

    @property
    def ollama_embedding_url(self) -> str:
        """Retorna URL completa para embedding."""
        return f"{self.OLLAMA_BASE_URL}"

    @property
    def ollama_llm_url(self) -> str:
        """Retorna URL completa para LLM."""
        return f"{self.OLLAMA_BASE_URL}"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância cacheada das configurações.
    Usa LRU cache para evitar múltiplas leituras do .env.
    """
    return Settings()


# Instância global de configurações
settings = get_settings()
