"""
Health Check - Verificação de saúde dos serviços.
"""

import logging
from typing import Dict, Any

from config import settings

logger = logging.getLogger(__name__)


async def check_ollama_health() -> Dict[str, Any]:
    """Verifica se Ollama está respondendo."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]

                return {
                    "status": "healthy",
                    "models_available": models,
                    "required_models": [settings.EMBEDDING_MODEL, settings.LLM_MODEL],
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"Ollama returned status {response.status_code}",
                }
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def check_database_health() -> Dict[str, Any]:
    """Verifica se PostgreSQL está respondendo."""
    try:
        from core.database import db_manager

        return db_manager.check_connection()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def full_health_check() -> Dict[str, Any]:
    """
    Verificação completa de saúde.
    """
    # Check database
    db_status = check_database_health()

    # Check Ollama
    ollama_status = await check_ollama_health()

    # Determine overall status
    is_healthy = (
        db_status.get("status") == "healthy"
        and ollama_status.get("status") == "healthy"
    )

    return {
        "status": "healthy" if is_healthy else "degraded",
        "version": "1.0.0",
        "services": {
            "database": {
                "status": db_status.get("status"),
                "detail": db_status.get("detail", "N/A"),
            },
            "ollama": {
                "status": ollama_status.get("status"),
                "models": ollama_status.get("models_available", []),
                "required": ollama_status.get("required_models", []),
            },
        },
    }
