"""
User-Aware RAG System
Each user has their own private knowledge base and conversation context
"""

from rag_system import RAGSystem
from user_manager import UserManager
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from openai import OpenAI
from config import Config

class UserRAGSystem:
    def __init__(self):
        self.config = Config()
        self.user_manager = UserManager()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize GPT-OSS client
        self.gpt_client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=self.config.HUGGINGFACE_API_TOKEN
        )
    
    def add_document_for_user(self, user_id: str, text: str, metadata: Dict[str, Any] = None) -> str:
        """Add document to user's private knowledge base"""
        if metadata is None:
            metadata = {}
        
        metadata["user_id"] = user_id
        
        # Get user's collection
        collection = self.user_manager.get_user_collection(user_id)
        
        # Split text into chunks
        chunks = self._split_text(text)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)
        
        # Create unique IDs
        doc_id = metadata.get('filename', 'doc')
        chunk_ids = [f"{user_id}_{doc_id}_chunk_{i}" for i in range(len(chunks))]
        
        # Add to user's collection
        collection.add(
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=[metadata] * len(chunks),
            ids=chunk_ids
        )
        
        # Update user stats
        self.user_manager.increment_document_count(user_id)
        
        return f"Added {len(chunks)} chunks to your private knowledge base"
    
    def query_with_context(self, user_id: str, question: str, channel: str = "whatsapp") -> str:
        """Query with conversation context (like ChatGPT)"""
        # Get conversation history
        context = self.user_manager.get_conversation_context(user_id, channel)
        
        # Search user's private knowledge base
        relevant_docs = self._search_user_documents(user_id, question)
        
        # Generate response with context
        response = self._generate_contextual_response(question, relevant_docs, context)
        
        # Save to conversation history
        self.user_manager.add_message_to_session(user_id, "user", question, channel)
        self.user_manager.add_message_to_session(user_id, "assistant", response, channel)
        
        return response
    
    def _search_user_documents(self, user_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search in user's private knowledge base"""
        try:
            collection = self.user_manager.get_user_collection(user_id)
            
            # Check if collection has documents
            if collection.count() == 0:
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Search
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=min(top_k, collection.count())
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'][0] else 0
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching user documents: {str(e)}")
            return []
    
    def _generate_contextual_response(self, question: str, docs: List[Dict], conversation_history: List[Dict]) -> str:
        """Generate response with conversation context"""
        # Prepare knowledge base context
        kb_context = "\n\n".join([doc['content'] for doc in docs]) if docs else "No relevant documents found."
        
        # Prepare conversation context
        conv_context = ""
        if conversation_history:
            recent_messages = conversation_history[-6:]  # Last 3 exchanges
            conv_context = "\n".join([
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in recent_messages
            ])
        
        # Create system prompt
        system_prompt = f"""You are a helpful AI assistant with access to the user's private knowledge base.

Previous conversation:
{conv_context if conv_context else "This is the start of the conversation."}

Knowledge base context:
{kb_context[:2000]}

Guidelines:
- Remember the conversation context and refer to it when relevant
- Answer based on the knowledge base when available
- If the answer isn't in the knowledge base, use your general knowledge
- Be conversational and remember what the user said earlier
- Keep responses concise and helpful"""

        try:
            response = self.gpt_client.chat.completions.create(
                model="openai/gpt-oss-20b:fireworks-ai",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                if content and content.strip():
                    return content.strip()
            
            raise Exception("Empty response from GPT-OSS")
            
        except Exception as e:
            print(f"GPT-OSS error: {str(e)}")
            # Fallback response
            if docs:
                return f"Based on your knowledge base:\n\n{docs[0]['content'][:500]}..."
            else:
                return "I don't have enough information in your knowledge base to answer that question. Try uploading relevant documents!"
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        return self.user_manager.get_user_stats(user_id)
    
    def clear_conversation(self, user_id: str, channel: str = "whatsapp"):
        """Clear conversation history"""
        self.user_manager.clear_session(user_id, channel)