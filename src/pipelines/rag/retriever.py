"""
Pipeline RAG - Recuperação de documentos e busca semântica.
"""

import logging
from typing import List, Optional, Dict
from dataclasses import dataclass

from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever

from config import settings
from pipelines.embedding.embedder import create_embedder

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Resultado de uma busca semântica."""

    documents: List[Document]
    scores: List[float]
    collection: str


class PGVectorStore:
    """
    Wrapper para PGVector que facilita recuperação de retrievers por collection.
    Uso do padrão padrão LangChain em vez de wrapper personalizado.
    """

    def __init__(self, embeddings: Optional[Embeddings] = None):
        """
        Inicializa o vector store.

        Args:
            embeddings: Função de embedding (usa BGE-M3 por padrão)
        """
        self.embeddings = embeddings or create_embedder().embeddings
        self._vectorstores: Dict[str, PGVector] = {}

    def _get_vectorstore(self, collection_name: str) -> PGVector:
        """
        Retorna instância do PGVector para uma collection.

        Args:
            collection_name: Nome da collection

        Returns:
            Instância de PGVector
        """
        if collection_name not in self._vectorstores:
            vectorstore = PGVector(
                collection_name=collection_name,
                connection_string=settings.DATABASE_URL,
                embedding_function=self.embeddings,
            )
            self._vectorstores[collection_name] = vectorstore

        return self._vectorstores[collection_name]

    def get_retriever(
        self,
        collection_name: str,
        k: Optional[int] = None,
        search_type: str = "similarity",
    ) -> BaseRetriever:
        """
        Retorna um retriever padrão LangChain para a collection.

        Args:
            collection_name: Nome da collection
            k: Número de documentos a retornar
            search_type: Tipo de busca ("similarity", "mmr", etc)

        Returns:
            BaseRetriever compatível com RetrievalQA
        """
        top_k = k or settings.TOP_K_RESULTS
        vectorstore = self._get_vectorstore(collection_name)

        # Usar as_retriever() do PGVector para retornar VectorStoreRetriever
        return vectorstore.as_retriever(
            search_kwargs={"k": top_k, "search_type": search_type}
        )

    def search(
        self, query: str, collection_name: str, k: Optional[int] = None
    ) -> SearchResult:
        """
        Busca documentos similares no banco vetorial.

        Args:
            query: Pergunta/string de busca
            collection_name: Collection específica
            k: Número de resultados (default do config)

        Returns:
            SearchResult com documentos e scores
        """
        top_k = k or settings.TOP_K_RESULTS

        if not collection_name:
            raise ValueError("collection_name é obrigatório")

        logger.info(f"Buscando em '{collection_name}' com k={top_k}")

        vectorstore = self._get_vectorstore(collection_name)

        # Busca por similaridade
        docs_and_scores = vectorstore.similarity_search_with_score(query=query, k=top_k)

        documents = [doc for doc, score in docs_and_scores]
        scores = [score for doc, score in docs_and_scores]

        logger.info(f"Encontrados {len(documents)} documentos")

        return SearchResult(
            documents=documents, scores=scores, collection=collection_name
        )

    def search_all_collections(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        k_per_collection: Optional[int] = None,
    ) -> Dict[str, SearchResult]:
        """
        Busca em múltiplas collections simultaneamente.

        Args:
            query: String de busca
            collections: Lista de collections (todas válidas por padrão)
            k_per_collection: Resultados por collection

        Returns:
            Dicionário com resultados por collection
        """
        if collections is None:
            collections = settings.valid_collections

        k_per_collection = k_per_collection or settings.TOP_K_RESULTS

        results = {}

        for collection in collections:
            try:
                result = self.search(
                    query=query, collection_name=collection, k=k_per_collection
                )
                results[collection] = result
            except Exception as e:
                logger.warning(f"Erro ao buscar em {collection}: {e}")
                results[collection] = None

        return results


# Singleton instance
_vector_store_instance: Optional[PGVectorStore] = None


def get_vector_store() -> PGVectorStore:
    """Factory function para criar/reutilizar PGVectorStore."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = PGVectorStore()
    return _vector_store_instance


def create_rag_retriever(collection_name: Optional[str] = None) -> PGVectorStore:
    """
    Factory function compatível com código existente.
    OBSOLETO: Use get_vector_store() em vez disso.
    """
    logger.warning(
        "create_rag_retriever() é obsoleto. Use get_vector_store() em vez disso."
    )
    return get_vector_store()
