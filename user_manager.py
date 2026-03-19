"""
User manager for user accounts, sessions, and private knowledge bases.
"""

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from config import Config

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or Config.USER_DATA_DIRECTORY
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.sessions_file = os.path.join(self.data_dir, "sessions.json")

        os.makedirs(self.data_dir, exist_ok=True)

        self.users = self._load_json(self.users_file)
        self.sessions = self._load_json(self.sessions_file)

        self.chroma_client = chromadb.PersistentClient(
            path=os.path.join(self.data_dir, "chroma_db"),
            settings=Settings(anonymized_telemetry=False),
        )

    def _load_json(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            return {}

        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to load %s: %s", path, exc)
            return {}

    def _save_users(self):
        self._atomic_write_json(self.users_file, self.users)

    def _save_sessions(self):
        self._atomic_write_json(self.sessions_file, self.sessions)

    def _atomic_write_json(self, path: str, payload: Dict[str, Any]):
        fd, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=self.data_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
            os.chmod(path, 0o600)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def get_or_create_user(self, phone_number: str, name: Optional[str] = None) -> Dict[str, Any]:
        user_id = self._hash_phone(phone_number)

        if user_id not in self.users:
            self.users[user_id] = {
                "user_id": user_id,
                "phone_number_last4": (phone_number or "")[-4:],
                "name": name or f"User_{user_id[:8]}",
                "created_at": datetime.now().isoformat(),
                "total_messages": 0,
                "total_documents": 0,
                "collection_name": f"user_{user_id}",
            }
            self._save_users()
            self._create_user_collection(user_id)

        return self.users[user_id]

    def _hash_phone(self, phone_number: str) -> str:
        return hashlib.sha256(phone_number.encode("utf-8")).hexdigest()[:16]

    def _create_user_collection(self, user_id: str):
        collection_name = f"user_{user_id}"
        try:
            self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            logger.warning("Error creating collection for %s: %s", user_id, exc)

    def get_user_collection(self, user_id: str):
        collection_name = f"user_{user_id}"
        try:
            return self.chroma_client.get_collection(name=collection_name)
        except Exception:
            self._create_user_collection(user_id)
            return self.chroma_client.get_collection(name=collection_name)

    def get_or_create_session(self, user_id: str, channel: str = "whatsapp") -> Dict[str, Any]:
        session_key = f"{user_id}_{channel}"

        if session_key not in self.sessions:
            self.sessions[session_key] = {
                "session_id": session_key,
                "user_id": user_id,
                "channel": channel,
                "started_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "messages": [],
                "context": [],
            }
            self._save_sessions()

        self.sessions[session_key]["last_activity"] = datetime.now().isoformat()
        self._save_sessions()
        return self.sessions[session_key]

    def add_message_to_session(
        self, user_id: str, role: str, content: str, channel: str = "whatsapp"
    ):
        session = self.get_or_create_session(user_id, channel)
        session["messages"].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if len(session["messages"]) > 10:
            session["messages"] = session["messages"][-10:]
        session["context"] = session["messages"][-10:]
        self._save_sessions()

        if user_id in self.users:
            self.users[user_id]["total_messages"] += 1
            self._save_users()

    def get_conversation_context(self, user_id: str, channel: str = "whatsapp") -> List[Dict[str, Any]]:
        session = self.get_or_create_session(user_id, channel)
        return session.get("context", [])

    def clear_session(self, user_id: str, channel: str = "whatsapp"):
        session_key = f"{user_id}_{channel}"
        if session_key in self.sessions:
            del self.sessions[session_key]
            self._save_sessions()

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.users:
            return {}

        user = self.users[user_id]
        collection = self.get_user_collection(user_id)
        return {
            "name": user["name"],
            "created_at": user["created_at"],
            "total_messages": user["total_messages"],
            "total_documents": collection.count(),
            "member_since": self._days_since(user["created_at"]),
        }

    def _days_since(self, date_str: str) -> int:
        created = datetime.fromisoformat(date_str)
        return (datetime.now() - created).days

    def increment_document_count(self, user_id: str):
        if user_id in self.users:
            self.users[user_id]["total_documents"] += 1
            self._save_users()

    def list_all_users(self) -> List[Dict[str, Any]]:
        return list(self.users.values())

    def delete_user_data(self, user_id: str):
        if user_id in self.users:
            del self.users[user_id]
            self._save_users()

        sessions_to_delete = [key for key in self.sessions if key.startswith(user_id)]
        for session_key in sessions_to_delete:
            del self.sessions[session_key]
        self._save_sessions()

        try:
            self.chroma_client.delete_collection(name=f"user_{user_id}")
        except Exception as exc:
            logger.warning("Error deleting collection for %s: %s", user_id, exc)
