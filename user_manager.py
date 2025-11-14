"""
User Manager for RAG Bot
Handles user accounts, sessions, and private knowledge bases
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import chromadb
from chromadb.config import Settings

class UserManager:
    def __init__(self, data_dir: str = "./user_data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.sessions_file = os.path.join(data_dir, "sessions.json")
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Load or initialize users and sessions
        self.users = self._load_users()
        self.sessions = self._load_sessions()
        
        # Initialize ChromaDB client for user collections
        self.chroma_client = chromadb.PersistentClient(
            path=os.path.join(data_dir, "chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )
    
    def _load_users(self) -> Dict:
        """Load users from file"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_users(self):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def _load_sessions(self) -> Dict:
        """Load sessions from file"""
        if os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    def get_or_create_user(self, phone_number: str, name: Optional[str] = None) -> Dict:
        """Get existing user or create new one"""
        user_id = self._hash_phone(phone_number)
        
        if user_id not in self.users:
            # Create new user
            self.users[user_id] = {
                "user_id": user_id,
                "phone_number": phone_number,
                "name": name or f"User_{user_id[:8]}",
                "created_at": datetime.now().isoformat(),
                "total_messages": 0,
                "total_documents": 0,
                "collection_name": f"user_{user_id}"
            }
            self._save_users()
            
            # Create user's private collection
            self._create_user_collection(user_id)
        
        return self.users[user_id]
    
    def _hash_phone(self, phone_number: str) -> str:
        """Hash phone number for privacy"""
        return hashlib.sha256(phone_number.encode()).hexdigest()[:16]
    
    def _create_user_collection(self, user_id: str):
        """Create a private ChromaDB collection for user"""
        collection_name = f"user_{user_id}"
        try:
            self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Error creating collection for {user_id}: {str(e)}")
    
    def get_user_collection(self, user_id: str):
        """Get user's private collection"""
        collection_name = f"user_{user_id}"
        return self.chroma_client.get_collection(name=collection_name)
    
    def get_or_create_session(self, user_id: str, channel: str = "whatsapp") -> Dict:
        """Get or create conversation session"""
        session_key = f"{user_id}_{channel}"
        
        if session_key not in self.sessions:
            self.sessions[session_key] = {
                "session_id": session_key,
                "user_id": user_id,
                "channel": channel,
                "started_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "messages": [],
                "context": []
            }
            self._save_sessions()
        
        # Update last activity
        self.sessions[session_key]["last_activity"] = datetime.now().isoformat()
        self._save_sessions()
        
        return self.sessions[session_key]
    
    def add_message_to_session(self, user_id: str, role: str, content: str, channel: str = "whatsapp"):
        """Add message to conversation history"""
        session = self.get_or_create_session(user_id, channel)
        
        message = {
            "role": role,  # "user" or "assistant"
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        session["messages"].append(message)
        
        # Keep only last 10 messages for context
        if len(session["messages"]) > 10:
            session["messages"] = session["messages"][-10:]
        
        # Update context (last 5 exchanges)
        session["context"] = session["messages"][-10:]
        
        self._save_sessions()
        
        # Update user stats
        if user_id in self.users:
            self.users[user_id]["total_messages"] += 1
            self._save_users()
    
    def get_conversation_context(self, user_id: str, channel: str = "whatsapp") -> List[Dict]:
        """Get recent conversation context"""
        session = self.get_or_create_session(user_id, channel)
        return session.get("context", [])
    
    def clear_session(self, user_id: str, channel: str = "whatsapp"):
        """Clear conversation session"""
        session_key = f"{user_id}_{channel}"
        if session_key in self.sessions:
            del self.sessions[session_key]
            self._save_sessions()
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        if user_id not in self.users:
            return {}
        
        user = self.users[user_id]
        collection = self.get_user_collection(user_id)
        
        return {
            "name": user["name"],
            "created_at": user["created_at"],
            "total_messages": user["total_messages"],
            "total_documents": collection.count(),
            "member_since": self._days_since(user["created_at"])
        }
    
    def _days_since(self, date_str: str) -> int:
        """Calculate days since date"""
        created = datetime.fromisoformat(date_str)
        return (datetime.now() - created).days
    
    def increment_document_count(self, user_id: str):
        """Increment user's document count"""
        if user_id in self.users:
            self.users[user_id]["total_documents"] += 1
            self._save_users()
    
    def list_all_users(self) -> List[Dict]:
        """List all users (admin function)"""
        return list(self.users.values())
    
    def delete_user_data(self, user_id: str):
        """Delete all user data (GDPR compliance)"""
        # Delete user record
        if user_id in self.users:
            del self.users[user_id]
            self._save_users()
        
        # Delete sessions
        sessions_to_delete = [k for k in self.sessions.keys() if k.startswith(user_id)]
        for session_key in sessions_to_delete:
            del self.sessions[session_key]
        self._save_sessions()
        
        # Delete collection
        try:
            collection_name = f"user_{user_id}"
            self.chroma_client.delete_collection(name=collection_name)
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")