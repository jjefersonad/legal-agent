"""
Pipeline de Embedding - Geração de vetores com Ollama (BGE-M3).
"""

import logging
from typing import List, Optional

from langchain_ollama import OllamaEmbeddings
from langchain_core.embeddings import Embeddings

from config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """
    Responsabilidade: Gerar vetores (embeddings) de textos.
    """

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Inicializa o embedder com Ollama BGE-M3.

        Args:
            model: Nome do modelo de embedding (default do config)
            base_url: URL do Ollama (default do config - porta 11434 com bge-m3)
        """
        self.model = model or settings.EMBEDDING_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL_EMBEDDING

        self._embeddings: Optional[Embeddings] = None  # type: ignore[assignment]

    @property
    def embeddings(self) -> Embeddings:
        """Lazy initialization do embeddings."""
        if self._embeddings is None:
            logger.info(f"Inicializando Ollama Embeddings: {self.model}")
            self._embeddings = OllamaEmbeddings(
                model=self.model, base_url=self.base_url
            )
        return self._embeddings

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para lista de textos.

        Args:
            texts: Lista de strings para vetorizar

        Returns:
            Lista de vetores (lista de floats)
        """
        logger.info(f"Gerando embeddings para {len(texts)} textos")
        vectors = self.embeddings.embed_documents(texts)
        logger.info(f"Embeddings gerados: shape={[len(v) for v in vectors]}")
        return vectors

    def embed_query(self, query: str) -> List[float]:
        """
        Gera embedding para uma query.

        Args:
            query: String de consulta

        Returns:
            Vetor de embedding
        """
        logger.info(f"Gerando embedding para query: '{query[:50]}...'")
        vector = self.embeddings.embed_query(query)
        logger.info(f"Embedding gerado: dimensão {len(vector)}")
        return vector

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Alias para embed_texts (API consistente).
        """
        return self.embed_texts(documents)


def create_embedder() -> Embedder:
    """Factory function para criar Embedder."""
    return Embedder()


class BatchEmbedder:
    """
    Embedder com suporte a processamento em lotes.
    Úil para grandes volumes de documentos.
    """

    def __init__(self, embedder: Optional[Embedder] = None, batch_size: int = 32):
        self.embedder = embedder or create_embedder()
        self.batch_size = batch_size

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Processa textos em batches para evitar sobrecarga.

        Args:
            texts: Lista de textos

        Returns:
            Lista de vetores
        """
        all_vectors = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            logger.info(f"Processando batch {batch_num}/{total_batches}")
            vectors = self.embedder.embed_texts(batch)
            all_vectors.extend(vectors)

        return all_vectors
