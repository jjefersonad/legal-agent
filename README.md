# Legal RAG API

API REST para sistema de Recuperação Augmentada por Geração (RAG) especializado em documentos jurídicos brasileiros.

## 🚀 Funcionalidades

- **Indexação de Documentos**: Processa PDFs jurídicos e armazena embeddings no PostgreSQL
- **Busca Semântica**: Pesquisa em código penal, constituição federal e outros documentos
- **Modo Híbrido de Busca**: 
  - Busca em TODAS as coleções simultaneamente
  - Busca em collection específica (penal ou constitucional)
- **Agente Jurídico**: Gera respostas fundamentadas com citação de fontes

## 📋 Pré-requisitos

- Docker & Docker Compose
- Python 3.12+
- Ollama rodando (bge-m3 para embeddings, qwen2.5:7b para LLM)

## 🛠️ Instalação

### 1. Clonar e configurar ambiente

```bash
cd legal-agent
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
```

### 2. Iniciar PostgreSQL com pgvector

```bash
docker compose up -d
```

### 3. Verificar Ollama

```bash
# Ollama deve estar rodando em localhost:11434
curl http://localhost:11434/api/tags

# Baixar modelos necessários
ollama pull bge-m3:latest
ollama pull qwen2.5:7b
```

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com suas configurações
```

## 📚 Indexação de Documentos

### Indexar Código Penal

```bash
curl -X POST "http://localhost:8000/api/v1/documents/codigo_penal" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/Codigo_penal_8ed.pdf"
  }'
```

### Indexar Constituição Federal

```bash
curl -X POST "http://localhost:8000/api/v1/documents/constituicao_federal" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/Constituicao_Federal_ate_a_EC_128-2022.pdf"
  }'
```

## 🔍 Realizar Buscas

### Busca em TODOS os documentos

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quais são os crimes contra a administração pública?"
  }'
```

### Busca no Código Penal

```bash
curl -X POST "http://localhost:8000/api/v1/search/codigo_penal" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Qual é a pena para o crime de peculato?"
  }'
```

### Busca na Constituição Federal

```bash
curl -X POST "http://localhost:8000/api/v1/search/constituicao_federal" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quais são os direitos fundamentais garantidos?"
  }'
```

## 🗂️ Gerenciar Coleções

### Listar todas as coleções

```bash
curl -X GET "http://localhost:8000/api/v1/collections"
```

### Ver informações de uma coleção

```bash
curl -X GET "http://localhost:8000/api/v1/collections/codigo_penal"
```

## 🏥 Health Check

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

## 📖 Documentação da API

Acesse `http://localhost:8000/docs` para ver a documentação interativa (Swagger UI).

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI                               │
│   POST /documents/{collection}  → Indexar documento         │
│   POST /search                 → Buscar em todos            │
│   POST /search/{collection}    → Buscar em específico       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      Agente Jurídico                         │
│   - Orquestra busca                                          │
│   - Formata prompts                                          │
│   - Gera respostas com fontes                                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Pipeline RAG                              │
│   - Embedding (bge-m3)                                       │
│   - Busca vetorial (pgvector)                                │
│   - Recuperação de contexto                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 PostgreSQL + pgvector                         │
│   Armazenamento de vetores e metadados                       │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estrutura de Pastas

```
legal-agent/
├── src/
│   ├── main.py                   # Entry point da aplicação
│   ├── config.py                 # Configurações centralizadas
│   ├── api/                      # Endpoints REST
│   │   └── routes/
│   │       ├── documents.py      # Indexação de documentos
│   │       ├── search.py         # Busca semântica
│   │       └── collections.py    # Gerenciamento de coleções
│   ├── pipelines/                # Processamento modular
│   │   ├── chunk/                # Chunking de documentos
│   │   ├── embedding/            # Geração de vetores
│   │   └── rag/                  # Recuperação e busca
│   ├── services/                 # Serviços de negócio
│   │   ├── indexer.py            # Orquestra indexação
│   │   ├── rag_service.py        # Orquestra RAG
│   │   └── agent.py              # Agente jurídico
│   ├── core/                     # Utilitários core
│   │   ├── database.py           # Conexão PostgreSQL
│   │   └── health.py             # Health checks
│   ├── domain/                   # Entidades e models
│   └── templates/                # Prompts do sistema
├── data/                         # PDFs jurídicos
├── docker-compose.yml            # PostgreSQL + pgvector
├── pyproject.toml             # Dependências e configuração Python
├── .env.example                  # Exemplo de variáveis
└── README.md                     # Este arquivo
```

## ⚙️ Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL de conexão PostgreSQL | postgresql+psycopg://postgres:password@localhost:5432/juridico_db |
| `OLLAMA_BASE_URL` | URL do Ollama | http://localhost:11434 |
| `EMBEDDING_MODEL` | Modelo para embeddings | bge-m3:latest |
| `LLM_MODEL` | Modelo de linguagem | qwen2.5:7b |
| `COLLECTION_PENAL` | Nome collection penal | codigo_penal |
| `COLLECTION_CONSTITUCIONAL` | Nome collection constitucional | constituicao_federal |
| `CHUNK_SIZE` | Tamanho dos chunks | 1000 |
| `CHUNK_OVERLAP` | Sobreposição dos chunks | 200 |
| `TOP_K_RESULTS` | Resultados por busca | 5 |

## 🧪 Executando a API

```bash
# Desenvolvimento com reload automático
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Produção
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 🧪 Testes

```bash
# Executar testes unitários
pytest tests/ -v

# Executar com coverage
pytest --cov=src tests/
```

## 📝 Licença

MIT License

## 👤 Autor

Jeferson