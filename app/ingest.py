from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from rag import RAGStore

DATA_DIR = Path("/data")


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def ingest_data(store: RAGStore) -> Dict[str, int]:
    if not DATA_DIR.exists():
        return {"files": 0, "chunks": 0}

    files = list(DATA_DIR.glob("*.txt")) + list(DATA_DIR.glob("*.md"))
    all_chunks: List[str] = []

    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = _chunk_text(text)
        all_chunks.extend(chunks)

    store.build(all_chunks)
    return {"files": len(files), "chunks": len(all_chunks)}
