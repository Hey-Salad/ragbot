"""
User-aware RAG system with per-user collections and conversation context.
"""

import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import Config
from embeddings import EmbeddingProvider
from security_utils import sanitize_filename
from user_manager import UserManager

logger = logging.getLogger(__name__)


class UserRAGSystem:
    def __init__(self):
        self.config = Config()
        self.user_manager = UserManager()
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

    def add_document_for_user(
        self, user_id: str, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a document to a user's private knowledge base."""
        clean_text = (text or "").strip()
        if not clean_text:
            raise ValueError("Document content is empty")

        metadata = dict(metadata or {})
        metadata["user_id"] = user_id
        collection = self.user_manager.get_user_collection(user_id)

        chunks = self._split_text(clean_text)
        embeddings = self.embedding_model.encode(chunks)
        doc_id = sanitize_filename(metadata.get("filename"), default="doc")
        chunk_ids = [f"{user_id}_{doc_id}_chunk_{index}" for index in range(len(chunks))]

        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=[metadata] * len(chunks),
            ids=chunk_ids,
        )

        self.user_manager.increment_document_count(user_id)
        return f"Added {len(chunks)} chunks to your private knowledge base"

    def query_with_context(self, user_id: str, question: str, channel: str = "whatsapp") -> str:
        """Query with short conversation memory."""
        context = self.user_manager.get_conversation_context(user_id, channel)
        relevant_docs = self._search_user_documents(user_id, question)
        response = self._generate_contextual_response(question, relevant_docs, context)

        self.user_manager.add_message_to_session(user_id, "user", question, channel)
        self.user_manager.add_message_to_session(user_id, "assistant", response, channel)
        return response

    def _search_user_documents(
        self, user_id: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        try:
            collection = self.user_manager.get_user_collection(user_id)
            if collection.count() == 0:
                return []

            query_embedding = self.embedding_model.encode([query])
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=min(top_k, collection.count()),
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
        except Exception as exc:
            logger.warning("Error searching user documents: %s", exc)
            return []

    def _generate_contextual_response(
        self, question: str, docs: List[Dict[str, Any]], conversation_history: List[Dict[str, Any]]
    ) -> str:
        kb_context = "\n\n".join(doc["content"] for doc in docs) if docs else "No relevant documents found."
        conv_context = ""
        if conversation_history:
            recent_messages = conversation_history[-6:]
            conv_context = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_messages
            )

        system_prompt = f"""You are a helpful AI assistant with access to the user's private knowledge base.

Previous conversation:
{conv_context if conv_context else "This is the start of the conversation."}

Knowledge base context:
{kb_context[:2000]}

Guidelines:
- Remember the conversation context and refer to it when relevant
- Answer based on the knowledge base when available
- If the answer is not in the knowledge base, say so clearly
- Keep responses concise and helpful"""

        if not self.gpt_client:
            return self._fallback_response(docs)

        try:
            response = self.gpt_client.chat.completions.create(
                model=self.config.HUGGINGFACE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                if content and content.strip():
                    return content.strip()
        except Exception as exc:
            logger.warning("User LLM response failed; using fallback response: %s", exc)

        return self._fallback_response(docs)

    def _fallback_response(self, docs: List[Dict[str, Any]]) -> str:
        if docs:
            return f"Based on your knowledge base:\n\n{docs[0]['content'][:500]}..."
        return "I do not have enough information in your knowledge base to answer that question."

    def _split_text(
        self, text: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None
    ) -> List[str]:
        words = text.split()
        if not words:
            return []

        chunk_size = chunk_size or self.config.CHUNK_SIZE
        overlap = overlap or self.config.CHUNK_OVERLAP
        step = max(chunk_size - overlap, 1)

        chunks = []
        for index in range(0, len(words), step):
            chunk = " ".join(words[index : index + chunk_size]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        return self.user_manager.get_user_stats(user_id)

    def clear_conversation(self, user_id: str, channel: str = "whatsapp"):
        self.user_manager.clear_session(user_id, channel)
