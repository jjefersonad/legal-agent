# Dockerfile multi-stage para Legal RAG System
FROM python:3.10-slim as base

# Configurações básicas
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app

# Stage de desenvolvimento
FROM base as development

WORKDIR /app

# Instalar dependências Python
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[database,docker,dev]"

# Copiar código fonte
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/data /app/models /app/logs && \
    chown -R app:app /app && \
    chmod +x /app/docker/wait-for-it.sh

USER app

EXPOSE 8000

# Comando de inicialização para desenvolvimento
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage de produção
FROM base as production

WORKDIR /app

# Copiar requirements e instalar dependências de produção
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[database,docker]"

# Copiar código fonte
COPY . .

# Criar diretórios e configurar permissões
RUN mkdir -p /app/data /app/models /app/logs && \
    useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Comando de inicialização para produção
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]