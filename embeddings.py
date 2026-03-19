import hashlib
import logging
import re
from typing import Iterable, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class HashingEmbedder:
    """Small deterministic fallback embedder for constrained environments."""

    def __init__(self, vector_size: int = 384):
        self.vector_size = vector_size

    def encode(self, texts: Iterable[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            vector = np.zeros(self.vector_size, dtype=float)
            for token in TOKEN_RE.findall((text or "").lower()):
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
                index = int.from_bytes(digest[:8], "big") % self.vector_size
                sign = 1.0 if digest[8] % 2 == 0 else -1.0
                vector[index] += sign

            norm = np.linalg.norm(vector)
            if norm:
                vector /= norm
            vectors.append(vector.tolist())
        return vectors


class EmbeddingProvider:
    def __init__(
        self,
        backend: str = "auto",
        model_name: str = "all-MiniLM-L6-v2",
        vector_size: int = 384,
    ):
        self.backend = backend
        self.model_name = model_name
        self.vector_size = vector_size
        self._model: Optional[object] = None
        self._hashing_embedder = HashingEmbedder(vector_size=vector_size)
        self.backend_name = "hashing"

    def encode(self, texts: Iterable[str]) -> List[List[float]]:
        text_list = list(texts)
        if not text_list:
            return []

        if self.backend == "hashing":
            return self._hashing_embedder.encode(text_list)

        model = self._load_model()
        if model is None:
            return self._hashing_embedder.encode(text_list)

        embeddings = model.encode(text_list)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return [list(row) for row in embeddings]

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self.backend_name = "sentence-transformers"
            logger.info("Using sentence-transformers embeddings backend")
            return self._model
        except Exception as exc:
            if self.backend == "sentence-transformers":
                logger.warning(
                    "Requested sentence-transformers backend is unavailable; "
                    "falling back to hashing embeddings: %s",
                    exc,
                )
            else:
                logger.info(
                    "sentence-transformers unavailable; using hashing embeddings: %s",
                    exc,
                )
            self.backend_name = "hashing"
            return None
