import os
import requests
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import PyPDF2
import io
from config import Config
from openai import OpenAI

class RAGSystem:
    def __init__(self):
        self.config = Config()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=self.config.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize GPT-OSS client (same as your HeySalad implementation)
        self.gpt_client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=self.config.HUGGINGFACE_API_TOKEN
        )
        
    def add_document(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """Add a document to the vector database"""
        if metadata is None:
            metadata = {}
            
        # Split text into chunks
        chunks = self._split_text(text)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)
        
        # Create unique IDs for chunks
        doc_id = metadata.get('filename', 'doc')
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        
        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=[metadata] * len(chunks),
            ids=chunk_ids
        )
        
        return f"Added {len(chunks)} chunks from document"
    
    def add_pdf_document(self, pdf_content: bytes, filename: str) -> str:
        """Extract text from PDF and add to vector database"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            metadata = {"filename": filename, "type": "pdf"}
            return self.add_document(text, metadata)
            
        except Exception as e:
            return f"Error processing PDF: {str(e)}"
    
    def search_documents(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if top_k is None:
            top_k = self.config.TOP_K_RESULTS
            
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k
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
    
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate response using GPT-OSS with RAG context (same approach as HeySalad)"""
        # Prepare context from retrieved documents
        context = "\n\n".join([doc['content'] for doc in context_docs])
        
        # Create system prompt for RAG
        system_prompt = f"""You are an intelligent AI assistant that answers questions based on provided context.

Context from knowledge base:
{context[:2000]}

Guidelines:
- Answer based only on the provided context
- If the answer isn't in the context, say so clearly
- Keep responses concise and helpful
- Cite relevant information from the context"""

        try:
            # Use GPT-OSS via Hugging Face router (same as your HeySalad implementation)
            response = self.gpt_client.chat.completions.create(
                model="openai/gpt-oss-20b:fireworks-ai",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            # Handle the response properly
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                if content and content.strip():
                    return content.strip()
            
            # Fallback if response is None or empty
            raise Exception("Empty response from GPT-OSS")
            
        except Exception as e:
            print(f"GPT-OSS error: {str(e)}")
            # Fallback to simple context-based response
            return self._generate_fallback_response(query, context_docs)
    
    def _generate_fallback_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate a simple response based on context when FlexaAI API is not available"""
        if not context_docs:
            return "I couldn't find any relevant information in the knowledge base to answer your question."
        
        # Simple keyword matching and context extraction
        context = "\n\n".join([doc['content'] for doc in context_docs])
        
        # Return the most relevant context with a note
        response = f"""Based on the documents in my knowledge base, here's what I found:

{context[:800]}{'...' if len(context) > 800 else ''}

📝 *Note: This is a direct excerpt from the knowledge base. For AI-generated responses, please configure the FlexaAI API endpoint correctly.*

**Query:** {query}
**Sources:** {len(context_docs)} document(s) found"""
        
        return response
    
    def query(self, question: str) -> str:
        """Main query method that combines search and generation"""
        # Search for relevant documents
        relevant_docs = self.search_documents(question)
        
        if not relevant_docs:
            return "I couldn't find any relevant information in the knowledge base to answer your question."
        
        # Generate response with context
        return self.generate_response(question, relevant_docs)
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks for better retrieval"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.config.CHUNK_SIZE - self.config.CHUNK_OVERLAP):
            chunk = " ".join(words[i:i + self.config.CHUNK_SIZE])
            chunks.append(chunk)
        
        return chunks
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        count = self.collection.count()
        return {
            "total_documents": count,
            "collection_name": self.collection.name
        }