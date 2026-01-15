"""RAG service for orchestrating retrieval and generation with Groq."""

from typing import Any, AsyncIterator

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough

from app.core.config import settings
from app.services.vector_service import VectorService


class RAGService:
    """Service for RAG orchestration with streaming support."""

    def __init__(self, vector_service: VectorService):
        """Initialize the RAG service."""
        self.vector_service = vector_service
        self.llm = ChatGroq(
            model=settings.groq_model,
            temperature=settings.groq_temperature,
            api_key=settings.groq_api_key,
            streaming=True,
        )

        # System prompt for grounded responses
        self.system_prompt = """You are a helpful technical support assistant that answers questions based on product manuals and documentation.

Your responses must:
1. Be accurate and based only on the provided context
2. Cite specific sections or pages when referencing information
3. If the context doesn't contain enough information, say so clearly
4. Be concise but complete
5. Use the source documents to provide precise technical details

Always ground your answers in the provided context. Do not make up information that isn't in the context."""

        # RAG prompt template
        self.rag_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                (
                    "human",
                    "Context from documentation:\n{context}\n\nQuestion: {question}\n\nAnswer based on the context above:",
                ),
            ]
        )

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        query: str,
    ) -> AsyncIterator[tuple[str, list[dict[str, Any]]]]:
        """
        Generate a streaming response using RAG.

        Args:
            messages: Chat history (list of {"role": "user/assistant", "content": "..."})
            query: Current user query

        Yields:
            Tuples of (text_chunk, sources) where sources is a list of source documents
        """
        # Retrieve relevant chunks
        retrieved_chunks = await self.vector_service.retrieve_parent_chunks(query)

        if not retrieved_chunks:
            yield ("I couldn't find relevant information in the documentation for your question.", [])
            return

        # Format context from retrieved chunks
        context_parts = []
        sources = []
        for chunk in retrieved_chunks:
            source_info = {
                "document_name": chunk["document_name"],
                "page_number": chunk.get("page_number"),
                "section_title": chunk.get("section_title"),
                "similarity": chunk.get("similarity", 0.0),
            }
            sources.append(source_info)

            context_text = chunk["content"]
            if chunk.get("section_title"):
                context_text = f"[{chunk['section_title']}]\n{context_text}"
            context_parts.append(context_text)

        context = "\n\n---\n\n".join(context_parts)

        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages[:-1]:  # Exclude the last message (current query)
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        # Build the chain
        chain = (
            {
                "context": lambda x: context,
                "question": lambda x: query,
                "chat_history": lambda x: langchain_messages,
            }
            | self.rag_prompt
            | self.llm
        )

        # Stream the response
        buffer = ""

        async for chunk in chain.astream({}):
            if not chunk.content:
                continue

            new_text = chunk.content

            if buffer.endswith(new_text):
                continue

            buffer += new_text
            yield (new_text, [])


    async def generate(
        self,
        messages: list[dict[str, str]],
        query: str,
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Generate a non-streaming response using RAG.

        Args:
            messages: Chat history
            query: Current user query

        Returns:
            Tuple of (response_text, sources)
        """
        # Retrieve relevant chunks
        retrieved_chunks = await self.vector_service.retrieve_parent_chunks(query)

        if not retrieved_chunks:
            return ("I couldn't find relevant information in the documentation for your question.", [])

        # Format context
        context_parts = []
        sources = []
        for chunk in retrieved_chunks:
            source_info = {
                "document_name": chunk["document_name"],
                "page_number": chunk.get("page_number"),
                "section_title": chunk.get("section_title"),
                "similarity": chunk.get("similarity", 0.0),
            }
            sources.append(source_info)

            context_text = chunk["content"]
            if chunk.get("section_title"):
                context_text = f"[{chunk['section_title']}]\n{context_text}"
            context_parts.append(context_text)

        context = "\n\n---\n\n".join(context_parts)

        # Convert messages
        langchain_messages = []
        for msg in messages[:-1]:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        # Generate response
        chain = (
            {
                "context": lambda x: context,
                "question": lambda x: query,
                "chat_history": lambda x: langchain_messages,
            }
            | self.rag_prompt
            | self.llm
        )

        response = await chain.ainvoke({})
        return (response.content, sources)
