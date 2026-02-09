"""
Serviço de Agente Jurídico - Gera respostas usando LLM + Contexto.
"""

import logging
from typing import Optional
from pydantic import BaseModel

from langchain_ollama import ChatOllama
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever

from config import settings
from services.rag_service import RAGService, create_rag_service

logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Resposta do agente jurídico."""

    question: str
    answer: str
    sources: list[dict]
    search_mode: str  # "all" or "specific"
    collection_used: Optional[str] = None


class JuridicalAgent:
    """
    Responsabilidade: Gerar resposta final usando LLM + contexto recuperado.
    """

    def __init__(
        self,
        rag_service: Optional[RAGService] = None,
        llm_model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """
        Inicializa agente com dependências.

        Args:
            rag_service: Serviço de RAG para recuperação de contexto
            llm_model: Nome do modelo LLM
            temperature: Temperatura do LLM
        """
        self.rag_service = rag_service or create_rag_service()
        self.llm_model = llm_model or settings.LLM_MODEL
        self.temperature = temperature or settings.LLM_TEMPERATURE

        # Inicializar LLM
        self._llm = None

    @property
    def llm(self):
        """Lazy initialization do LLM."""
        if self._llm is None:
            logger.info(f"Inicializando LLM: {self.llm_model}")
            self._llm = ChatOllama(
                model=self.llm_model,
                temperature=self.temperature,
                base_url=settings.OLLAMA_BASE_URL_LLM,
            )
        return self._llm

    def _get_system_prompt(self) -> str:
        """
        Retorna prompt do sistema para agente jurídico.
        """
        return """Você é um assistente jurídico especialista, treinado para analisar legislação e doutrina brasileira.

INSTRUÇÕES:
- Responda à pergunta do usuário baseando-se **exclusivamente** nos contextos fornecidos abaixo.
- Se a resposta não estiver no contexto, informe claramente que o documento não contém essa informação.
- Utilize linguagem formal jurídica em português brasileiro.
- Cite sempre a fonte (documento e página) para fundamentar a resposta.
- Seja preciso, objetivo e fundamentado legalmente.

Contextos:
{context}

Pergunta: {question}

Resposta (com citação de fontes):"""

    def _create_qa_chain(self, retriever: Optional[BaseRetriever] = None):
        """
        Cria cadeia de QA com prompt customizado.

        Args:
            retriever: BaseRetriever compatível com RetrievalQA
        """
        prompt = PromptTemplate(
            template=self._get_system_prompt(), input_variables=["context", "question"]
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

        return qa_chain

    def ask(
        self,
        question: str,
        search_mode: str = "all",
        collection: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> AgentResponse:
        """
        Processa pergunta e retorna resposta do agente.

        Args:
            question: Pergunta jurídica do usuário
            search_mode: "all" para todas as collections, "specific" para uma
            collection: Collection específica (requer search_mode="specific")
            top_k: Número de documentos a recuperar

        Returns:
            AgentResponse com resposta e fontes
        """
        logger.info(f"Processando pergunta: '{question[:50]}...'")
        logger.info(f"Search mode: {search_mode}, Collection: {collection}")

        # 2. Preparar retriever
        if search_mode == "all":
            # Buscar em todas as collections usando EnsembleRetriever
            retriever = self.rag_service.get_multi_retriever(
                collections=settings.valid_collections,
                k=top_k or settings.TOP_K_RESULTS,
            )
            collection_for_display = None
            search_mode_display = "Todas as collections"
        else:
            if not collection:
                raise ValueError("Collection é obrigatória para search_mode='specific'")
            # Buscar em uma collection específica
            retriever = self.rag_service.get_retriever(collection, k=top_k)
            collection_for_display = collection
            search_mode_display = f"Collection: {collection}"

        # 3. Gerar resposta com LLM usando o retriever apropriado
        qa_chain = self._create_qa_chain(retriever=retriever)

        result = qa_chain.invoke({"query": question})

        # 4. Formatar resposta
        answer = result.get("result", "Erro ao gerar resposta.")

        # 5. Formatar fontes
        sources = []
        for doc in result.get("source_documents", []):
            source = {
                "content": doc.page_content[:200] + "...",
                "page": doc.metadata.get("page", "N/A"),
                "source": doc.metadata.get("source", collection or "múltiplas"),
                "collection": doc.metadata.get("_collection", collection),
            }
            sources.append(source)

        return AgentResponse(
            question=question,
            answer=answer,
            sources=sources,
            search_mode=search_mode_display,
            collection_used=collection_for_display,
        )

    def ask_with_context(self, question: str, context: str) -> AgentResponse:
        """
        Gera resposta usando contexto pré-recuperado.
        Útil quando o contexto já foi obtido externamente.
        """
        logger.info("Gerando resposta com contexto fornecido")

        # Criar chain temporário sem retriever
        from langchain_classic.chains import LLMChain
        from langchain_core.prompts import PromptTemplate

        prompt = PromptTemplate(
            template=self._get_system_prompt(), input_variables=["context", "question"]
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        answer = chain.run({"context": context, "question": question})

        return AgentResponse(
            question=question,
            answer=answer.strip(),
            sources=[{"type": "provided_context"}],
            search_mode="provided_context",
            collection_used=None,
        )


def create_juridical_agent() -> JuridicalAgent:
    """Factory function para criar JuridicalAgent."""
    return JuridicalAgent()
