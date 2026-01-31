from __future__ import annotations

import os
from typing import Any, List

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ingest import ingest_data
from rag import RAGStore

app = FastAPI(title="ConstellationRAG", version="1.0.0")

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "http://nim:8000")
NIM_TIMEOUT = float(os.getenv("NIM_TIMEOUT", "120"))
TOP_K = int(os.getenv("TOP_K", "4"))
NIM_MODEL_ID = os.getenv("NIM_MODEL_ID", "meta/llama-3.2-1b-instruct")

rag_store = RAGStore()


class IngestResponse(BaseModel):
    files: int
    chunks: int


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[dict]
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, alias="max_tokens")
    top_p: float | None = None
    stream: bool | None = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    result = ingest_data(rag_store)
    return IngestResponse(files=result["files"], chunks=result["chunks"])


@app.post("/v1/chat/completions")
async def chat_completions(payload: ChatCompletionRequest) -> Any:
    if not rag_store.is_ready:
        raise HTTPException(status_code=400, detail="RAG index is empty. Call /ingest first.")

    user_messages = [m for m in payload.messages if m.get("role") == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found.")

    query = user_messages[-1].get("content", "")
    if not query:
        raise HTTPException(status_code=400, detail="User message content is empty.")

    contexts = rag_store.search(query, top_k=TOP_K)
    context_block = "\n\n".join(contexts)

    system_prompt = (
        "You are a helpful assistant. Use the provided context to answer the user. "
        "If the answer is not in the context, say you do not know.\n\n"
        f"Context:\n{context_block}"
    )

    new_messages = [{"role": "system", "content": system_prompt}] + payload.messages

    model_name = NIM_MODEL_ID if payload.model == "nim" else payload.model
    request_json = {
        "model": model_name,
        "messages": new_messages,
        "temperature": payload.temperature,
        "max_tokens": payload.max_tokens,
        "top_p": payload.top_p,
        "stream": payload.stream,
    }

    async with httpx.AsyncClient(timeout=NIM_TIMEOUT) as client:
        try:
            response = await client.post(f"{NIM_BASE_URL}/v1/chat/completions", json=request_json)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"NIM error: {exc}") from exc

    return response.json()
