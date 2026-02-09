"""
Conexão e utilitários de banco de dados PostgreSQL + pgvector.
"""

import logging
from typing import Optional
from contextlib import contextmanager

import psycopg
from psycopg_pool import AsyncConnectionPool, ConnectionPool

from config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador de conexões PostgreSQL."""

    def __init__(self):
        self._sync_pool: Optional[ConnectionPool] = None
        self._async_pool: Optional[AsyncConnectionPool] = None

    @property
    def connection_string(self) -> str:
        """Retorna string de conexão formatada."""
        return settings.DATABASE_URL

    def _create_sync_pool(self) -> ConnectionPool:
        """Cria pool de conexões síncrono."""
        if self._sync_pool is None:
            self._sync_pool = ConnectionPool(
                self.connection_string, min_size=2, max_size=10, timeout=30, open=True
            )
            logger.info("Sync connection pool created")
        return self._sync_pool

    def _create_async_pool(self) -> AsyncConnectionPool:
        """Cria pool de conexões assíncrono."""
        if self._async_pool is None:
            self._async_pool = AsyncConnectionPool(
                self.connection_string, min_size=2, max_size=10, timeout=30, open=True
            )
            logger.info("Async connection pool created")
        return self._async_pool

    @contextmanager
    def get_sync_connection(self):
        """
        Context manager para conexão síncrona.
        Uso:
            with db.get_sync_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
        """
        pool = self._create_sync_pool()
        with pool.connection() as conn:
            yield conn

    async def get_async_connection(self):
        """
        Retorna conexão assíncrona.
        Uso:
            async with db.get_async_connection() as conn:
                await conn.execute("SELECT 1")
        """
        pool = self._create_async_pool()
        return await pool.connection()

    def check_connection(self) -> dict:
        """Verifica status da conexão com o banco."""
        try:
            with self.get_sync_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return {
                        "status": "healthy",
                        "database": "connected",
                        "detail": "Connection successful",
                    }
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return {"status": "unhealthy", "database": "disconnected", "detail": str(e)}

    def close(self):
        """Fecha todos os pools de conexão."""
        if self._sync_pool:
            self._sync_pool.close()
            logger.info("Sync connection pool closed")
        if self._async_pool:
            self._async_pool.close()
            logger.info("Async connection pool closed")


# Instância global do gerenciador de banco
db_manager = DatabaseManager()


def check_database_health() -> dict:
    """Helper function para health check."""
    return db_manager.check_connection()
