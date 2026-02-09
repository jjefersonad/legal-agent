# Makefile para Legal RAG API

.PHONY: run dev test install check-models check-db

# Executar aplicação em produção
run:
	@echo "Executando Legal RAG API..."
	@python setup.py

# Executar com reload em desenvolvimento
dev:
	@echo "Executando em modo desenvolvimento..."
	@PYTHONPATH=/home/jeferson/projetos/IA/legal-agent/src python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Verificar modelos disponíveis no Ollama
check-models:
	@echo "Verificando modelos disponíveis no Ollama..."
	@curl -s http://localhost:12434/api/tags | python -m json.tool

# Verificar status do Ollama
check-ollama:
	@echo "Verificando status do Ollama..."
	@curl -s http://localhost:12434/api/status | python -m json.tool

# Verificar saúde da aplicação
test:
	@echo "Testando saúde da aplicação..."
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool

# Verificar informações da aplicação
info:
	@echo "Obtendo informações da aplicação..."
	@curl -s http://localhost:8000/api/v1/info | python -m json.tool

# Instalar dependências
install:
	@echo "Instalando dependências..."
	@pip install -r requirements.txt

# Limpar cache Python
clean:
	@echo "Limpando cache Python..."
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete

# Ajuda
help:
	@echo "Comandos disponíveis:"
	@echo "  make run      - Executar aplicação produção"
	@echo "  make dev      - Executar com reload desenvolvimento"
	@echo "  make test     - Testar saúde da aplicação"
	@echo "  make info     - Obter informações da aplicação"
	@echo "  make check-models - Verificar modelos Ollama"
	@echo "  make check-ollama - Verificar status Ollama"
	@echo "  make install  - Instalar dependências"
	@echo "  make clean    - Limpar cache Python"
	@echo "  make help     - Mostrar esta ajuda"