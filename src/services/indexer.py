"""
Serviço de Indexação - Orquestra Chunk → Embedding → PostgreSQL.
"""

import logging
import time
from typing import List, Optional
from pathlib import Path

from langchain_core.documents import Document

from config import settings
from pipelines.chunk.pdf_chunker import PDFChunker, create_pdf_chunker
from pipelines.embedding.embedder import Embedder, create_embedder
from pipelines.rag.retriever import PGVectorStore, get_vector_store

logger = logging.getLogger(__name__)


class IndexingResult:
    """Resultado do processo de indexação."""

    def __init__(
        self,
        collection: str,
        chunks_created: int,
        embeddings_generated: int,
        processing_time: float,
        status: str = "success",
    ):
        self.collection = collection
        self.chunks_created = chunks_created
        self.embeddings_generated = embeddings_generated
        self.processing_time = processing_time
        self.status = status


class IndexerService:
    """
    Responsabilidade: Orquestrar pipeline de indexação.
    CHUNK → EMBEDDING → PERSISTÊNCIA
    """

    def __init__(
        self,
        chunker: Optional[PDFChunker] = None,
        embedder: Optional[Embedder] = None,
        vector_store: Optional[PGVectorStore] = None,
    ):
        """
        Inicializa serviço com dependências injetadas.

        Args:
            chunker: Pipeline de chunking
            embedder: Pipeline de embedding
            vector_store: Acesso ao banco vetorial
        """
        self.chunker = chunker or create_pdf_chunker()
        self.embedder = embedder or create_embedder()
        self.vector_store = vector_store or get_vector_store()

    def index_document(
        self, file_path: str, collection_name: str, pre_delete_collection: bool = False
    ) -> IndexingResult:
        """
        Pipeline completo de indexação de documento.

        Args:
            file_path: Caminho do PDF
            collection_name: Nome da collection de destino
            pre_delete_collection: Se True, apaga collection existente

        Returns:
            IndexingResult com métricas
        """
        start_time = time.time()

        logger.info(f"Iniciando indexação: {file_path} → {collection_name}")

        # Validação
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        # Step 1: Chunking
        logger.info("Step 1: Chunking PDF...")
        chunks = self.chunker.process_pdf(file_path)
        logger.info(f"Chunks criados: {len(chunks)}")

        # Step 2: Embedding
        logger.info("Step 2: Gerando embeddings...")
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedder.embed_texts(texts)
        logger.info(f"Embeddings gerados: {len(embeddings)}")

        # Step 3: Persistência no PostgreSQL (pgvector)
        logger.info("Step 3: Persistindo no PostgreSQL...")
        from langchain_community.vectorstores import PGVector

        # Configurar collection (opcionalmente deletar existente)
        if pre_delete_collection:
            try:
                existing = PGVector(
                    collection_name=collection_name,
                    connection_string=settings.DATABASE_URL,
                    embedding_function=self.embedder.embeddings,
                )
                # Nota: PGVector não tem método direto para delete collection
                # Em produção, usar SQL direto
                logger.info(
                    f"Collection '{collection_name}' será mantida (append mode)"
                )
            except Exception:
                pass

        # Criar/atualizar collection
        vectorstore = PGVector.from_documents(
            documents=chunks,
            embedding=self.embedder.embeddings,
            collection_name=collection_name,
            connection_string=settings.DATABASE_URL,
            pre_delete_collection=pre_delete_collection,
        )

        processing_time = time.time() - start_time

        result = IndexingResult(
            collection=collection_name,
            chunks_created=len(chunks),
            embeddings_generated=len(embeddings),
            processing_time=round(processing_time, 2),
            status="success",
        )

        logger.info(f"Indexação concluída: {result}")
        return result

    def index_multiple_documents(
        self,
        documents: List[tuple[str, str]],  # [(file_path, collection), ...]
        pre_delete: bool = False,
    ) -> List[IndexingResult]:
        """
        Indexa múltiplos documentos.

        Args:
            documents: Lista de tuplas (file_path, collection_name)
            pre_delete: Se True, deleta cada collection antes de indexar

        Returns:
            Lista de resultados
        """
        results = []

        for file_path, collection in documents:
            try:
                result = self.index_document(
                    file_path=file_path,
                    collection_name=collection,
                    pre_delete_collection=pre_delete,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Erro ao indexar {file_path}: {e}")
                results.append(
                    IndexingResult(
                        collection=collection,
                        chunks_created=0,
                        embeddings_generated=0,
                        processing_time=0,
                        status="error",
                    )
                )

        return results


def create_indexer_service() -> IndexerService:
    """Factory function para criar IndexerService."""
    return IndexerService()


# Helper para import
def create_rag_retriever(collection_name: Optional[str] = None):
    from pipelines.rag.retriever import create_rag_retriever as _create

    return _create(collection_name)
