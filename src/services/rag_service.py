"""
Serviço RAG - Recuperação de contexto para geração de respostas.
"""

import logging
from typing import List, Optional, Dict
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from config import settings
from pipelines.embedding.embedder import create_embedder
from pipelines.rag.retriever import PGVectorStore, get_vector_store, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class ContextResult:
    """Contexto recuperado para resposta."""

    documents: List[Document]
    combined_context: str
    sources_meta: List[dict]
    collection: Optional[str] = None


class RAGService:
    """
    Responsabilidade: Orquestrar recuperação de contexto.
    """

    def __init__(self, vector_store: Optional[PGVectorStore] = None):
        """
        Inicializa serviço com vector store injetado.

        Args:
            vector_store: Instância de PGVectorStore
        """
        self.vector_store = vector_store or get_vector_store()
        self.embedder = create_embedder()

    def get_retriever(
        self, collection_name: str, k: Optional[int] = None
    ) -> BaseRetriever:
        """
        Retorna um retriever compatível com LangChain para uma collection.

        Args:
            collection_name: Nome da collection
            k: Número de documentos a retornar

        Returns:
            BaseRetriever compatível com RetrievalQA
        """
        return self.vector_store.get_retriever(collection_name, k=k)

    def get_multi_retriever(
        self, collections: List[str], k: Optional[int] = None
    ) -> BaseRetriever:
        """
        Retorna um retriever que busca em múltiplas collections.

        Args:
            collections: Lista de collections
            k: Número de documentos por collection

        Returns:
            EnsembleRetriever combinado
        """
        from langchain_classic.retrievers import EnsembleRetriever
        from typing import Sequence

        k_per_collection = k or settings.TOP_K_RESULTS

        # Criar retrievers para cada collection
        retrievers: Sequence[BaseRetriever] = [
            self.vector_store.get_retriever(coll, k=k_per_collection)
            for coll in collections
        ]

        # EnsembleRetriever aceita list[RetrieverLike]
        # BaseRetriever é compatível
        ensemble = EnsembleRetriever(
            retrievers=list(retrievers),  # type: ignore[arg-type]
            weights=[1.0] * len(retrievers),  # Peso igual para todos
        )

        return ensemble

    def get_context_from_collection(
        self, query: str, collection_name: str, k: Optional[int] = None
    ) -> ContextResult:
        """
        Recupera contexto de uma collection específica.

        Args:
            query: Pergunta do usuário
            collection_name: Collection de destino
            k: Número de documentos

        Returns:
            ContextResult com documentos e contexto formatado
        """
        top_k = k or settings.TOP_K_RESULTS

        logger.info(f"Recuperando contexto de '{collection_name}'")

        result = self.vector_store.search(
            query=query, collection_name=collection_name, k=top_k
        )

        # Formatar metadados das fontes
        sources_meta = []
        for i, doc in enumerate(result.documents):
            meta = {
                "index": i + 1,
                "page": doc.metadata.get("page", "N/A"),
                "source": doc.metadata.get("source", collection_name),
                "score": round(result.scores[i], 4),
            }
            sources_meta.append(meta)

        # Combinar documentos em contexto único
        combined_context = self._format_context(result.documents)

        return ContextResult(
            documents=result.documents,
            combined_context=combined_context,
            sources_meta=sources_meta,
            collection=collection_name,
        )

    def get_context_all_collections(
        self, query: str, k_per_collection: Optional[int] = None
    ) -> Dict[str, ContextResult]:
        """
        Recupera contexto de TODAS as collections.

        Args:
            query: Pergunta do usuário
            k_per_collection: Documentos por collection

        Returns:
            Dicionário com resultados por collection
        """
        k_per_collection = k_per_collection or settings.TOP_K_RESULTS
        collections = settings.valid_collections

        logger.info(f"Recuperando contexto de {len(collections)} collections")

        results = {}

        for collection in collections:
            try:
                result = self.get_context_from_collection(
                    query=query, collection_name=collection, k=k_per_collection
                )
                results[collection] = result
            except Exception as e:
                logger.warning(f"Erro ao recuperar de {collection}: {e}")
                results[collection] = None

        return results

    def _format_context(self, documents: List[Document]) -> str:
        """
        Formata lista de documentos em contexto único.

        Args:
            documents: Lista de documentos

        Returns:
            String formatada com todos os contextos
        """
        context_parts = []

        for i, doc in enumerate(documents):
            page = doc.metadata.get("page", "?")
            content = doc.page_content.strip()
            part = f"[Documento {i+1} - Página {page}]\n{content}"
            context_parts.append(part)

        return "\n\n".join(context_parts)

    def get_combined_context(
        self, query: str, collection: Optional[str] = None
    ) -> ContextResult:
        """
        Retorna contexto unificado (collection específica ou todas).

        Args:
            query: Pergunta
            collection: Collection específica (None = todas)

        Returns:
            ContextResult unificado
        """
        if collection:
            return self.get_context_from_collection(query, collection)
        else:
            all_results = self.get_context_all_collections(query)

            # Combinar resultados de todas as collections
            all_docs = []
            all_sources = []
            combined = []

            for coll_name, result in all_results.items():
                if result:
                    all_docs.extend(result.documents)
                    # Marcar origem no metadado
                    for doc in result.documents:
                        doc.metadata["_collection"] = coll_name
                    all_sources.extend(result.sources_meta)
                    combined.append(
                        f"=== {coll_name.upper()} ===\n{result.combined_context}"
                    )

            unified_context = "\n\n".join(combined)

            return ContextResult(
                documents=all_docs,
                combined_context=unified_context,
                sources_meta=all_sources,
                collection=None,  # Indica que é de múltiplas collections
            )


def create_rag_service() -> RAGService:
    """Factory function para criar RAGService."""
    return RAGService()
