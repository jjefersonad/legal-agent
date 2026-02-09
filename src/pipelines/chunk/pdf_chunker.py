"""
Pipeline de Chunking - Processamento de documentos PDF em chunks.
"""

import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import settings

logger = logging.getLogger(__name__)


class PDFChunker:
    """
    Responsabilidade: Carregar PDF e dividir em chunks semanticamente coerentes.
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Inicializa o chunker.

        Args:
            chunk_size: Tamanho de cada chunk (default do config)
            chunk_overlap: Sobreposição entre chunks (default do config)
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def load_pdf(self, file_path: str) -> List[Document]:
        """
        Carrega documento PDF e extrai texto.

        Args:
            file_path: Caminho do arquivo PDF

        Returns:
            Lista de documentos (páginas)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        logger.info(f"Carregando PDF: {file_path}")
        loader = PyPDFLoader(str(path))
        documents = loader.load()
        logger.info(f"PDF carregado: {len(documents)} páginas")

        return documents

    def split_documents(
        self, documents: List[Document], add_page_metadata: bool = True
    ) -> List[Document]:
        """
        Divide documentos em chunks menores.

        Args:
            documents: Lista de documentos (páginas)
            add_page_metadata: Se True, mantém metadados de página

        Returns:
            Lista de chunks processados
        """
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Documentos divididos em {len(chunks)} chunks")

        return chunks

    def process_pdf(self, file_path: str) -> List[Document]:
        """
        Pipeline completo: Carrega PDF e divide em chunks.

        Args:
            file_path: Caminho do arquivo PDF

        Returns:
            Lista de chunks prontos para embedding
        """
        # 1. Carrega PDF
        documents = self.load_pdf(file_path)

        # 2. Divide em chunks
        chunks = self.split_documents(documents)

        logger.info(f"Processamento completo: {len(chunks)} chunks gerados")
        return chunks


def create_pdf_chunker() -> PDFChunker:
    """Factory function para criar PDFChunker."""
    return PDFChunker()
