import io
import logging
from typing import Any, Dict, List, Optional

import chromadb
import PyPDF2
from chromadb.config import Settings
from openai import OpenAI

from config import Config
from embeddings import EmbeddingProvider
from security_utils import sanitize_filename

logger = logging.getLogger(__name__)


class RAGSystem:
    def __init__(self):
        self.config = Config()

        self.chroma_client = chromadb.PersistentClient(
            path=self.config.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_model = EmbeddingProvider(
            backend=self.config.EMBEDDING_BACKEND,
        )
        self.gpt_client = (
            OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=self.config.HUGGINGFACE_API_TOKEN,
                timeout=self.config.REQUEST_TIMEOUT_SECONDS,
            )
            if self.config.HUGGINGFACE_API_TOKEN
            else None
        )

    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a document to the vector database."""
        clean_text = (text or "").strip()
        if not clean_text:
            raise ValueError("Document content is empty")

        metadata = dict(metadata or {})
        chunks = self._split_text(clean_text)
        if not chunks:
            raise ValueError("Document content is empty after preprocessing")

        embeddings = self.embedding_model.encode(chunks)
        doc_id = sanitize_filename(metadata.get("filename"), default="doc")
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=[metadata] * len(chunks),
            ids=chunk_ids,
        )

        return f"Added {len(chunks)} chunks from document"

    def add_pdf_document(self, pdf_content: bytes, filename: str) -> str:
        """Extract text from PDF and add to vector database."""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text_parts: List[str] = []

            for page in pdf_reader.pages:
                text_parts.append(page.extract_text() or "")

            metadata = {"filename": sanitize_filename(filename), "type": "pdf"}
            return self.add_document("\n".join(text_parts), metadata)
        except Exception as exc:
            logger.exception("Error processing PDF document")
            raise ValueError("Unable to process PDF document") from exc

    def search_documents(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for relevant documents."""
        query = (query or "").strip()
        if not query or self.collection.count() == 0:
            return []

        top_k = top_k or self.config.TOP_K_RESULTS
        query_embedding = self.embedding_model.encode([query])
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
        )

        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for index, doc in enumerate(results["documents"][0]):
                formatted_results.append(
                    {
                        "content": doc,
                        "metadata": results["metadatas"][0][index] if results["metadatas"][0] else {},
                        "distance": results["distances"][0][index] if results["distances"][0] else 0,
                    }
                )

        return formatted_results

    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate a response using retrieved context."""
        if not context_docs:
            return self._generate_fallback_response(query, context_docs)

        context = "\n\n".join(doc["content"] for doc in context_docs)
        system_prompt = f"""You are an intelligent AI assistant that answers questions based on provided context.

Context from knowledge base:
{context[:2000]}

Guidelines:
- Answer based only on the provided context
- If the answer isn't in the context, say so clearly
- Keep responses concise and helpful
- Cite relevant information from the context"""

        if not self.gpt_client:
            return self._generate_fallback_response(query, context_docs)

        try:
            response = self.gpt_client.chat.completions.create(
                model=self.config.HUGGINGFACE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                max_tokens=300,
                temperature=0.7,
            )
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                if content and content.strip():
                    return content.strip()
        except Exception as exc:
            logger.warning("LLM response failed; using fallback response: %s", exc)

        return self._generate_fallback_response(query, context_docs)

    def _generate_fallback_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate a simple response based on retrieved context."""
        if not context_docs:
            return "I couldn't find any relevant information in the knowledge base to answer your question."

        context = "\n\n".join(doc["content"] for doc in context_docs)
        return (
            "Based on the documents in the knowledge base, here's what I found:\n\n"
            f"{context[:800]}{'...' if len(context) > 800 else ''}\n\n"
            f"Query: {query}\n"
            f"Sources: {len(context_docs)} document(s) found"
        )

    def query(self, question: str) -> str:
        """Search for relevant context and generate a response."""
        relevant_docs = self.search_documents(question)
        if not relevant_docs:
            return "I couldn't find any relevant information in the knowledge base to answer your question."
        return self.generate_response(question, relevant_docs)

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks for retrieval."""
        words = text.split()
        if not words:
            return []

        chunks = []
        step = max(self.config.CHUNK_SIZE - self.config.CHUNK_OVERLAP, 1)
        for index in range(0, len(words), step):
            chunk = " ".join(words[index : index + self.config.CHUNK_SIZE]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection."""
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name,
            "embedding_backend": self.embedding_model.backend_name,
            "llm_enabled": bool(self.gpt_client),
        }
