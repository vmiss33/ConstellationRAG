from __future__ import annotations

from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class RAGStore:
    def __init__(self) -> None:
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        self._index = None
        self._texts: List[str] = []

    @property
    def is_ready(self) -> bool:
        return self._index is not None and len(self._texts) > 0

    def build(self, chunks: List[str]) -> None:
        if not chunks:
            self._index = None
            self._texts = []
            return

        embeddings = self._model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        self._index = index
        self._texts = chunks

    def search(self, query: str, top_k: int = 4) -> List[str]:
        if not self.is_ready:
            return []

        query_vec = self._model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = self._index.search(query_vec, top_k)
        results: List[str] = []
        for idx in indices[0]:
            if 0 <= idx < len(self._texts):
                results.append(self._texts[idx])
        return results
