from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import os
import httpx

from langchain_core.prompts import ChatPromptTemplate

# Imports locales
from schemas import (
    Message, ChatRequest, ChatResponse, 
    EmbeddingsRequest, EmbeddingsResponse, PullRequest
)
from helpers import (
    OLLAMA_BASE, DEFAULT_MODEL, ALLOWED_MODELS, BASE_SYSTEM,
    ensure_model_allowed, get_chat, get_embedder
)

app = FastAPI(title="LangChain BFF over Ollama (multi-model)", version="1.0.0")

# --- CORS ---
origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if origins == ["*"] else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "{system}"),
    ("user", "{user}"),
])

# --- Routes ---
@app.get("/health")
async def health():
    return {"status": "ok", "default_model": DEFAULT_MODEL, "ollama_base": OLLAMA_BASE}

@app.get("/models")
async def list_models():
    # proxy a /api/tags de Ollama
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{OLLAMA_BASE}/api/tags")
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    data = r.json()
    tags = [item.get("name") for item in data.get("models", []) if item.get("name")]
    return {"models": tags, "allowed": ALLOWED_MODELS or "ANY"}

@app.post("/pull")
async def pull_model(req: PullRequest):
    payload = {"name": req.name}
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/pull", json=payload)
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return {"status": "ok", "pulled": req.name}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    model = ensure_model_allowed(req.model or DEFAULT_MODEL)

    system_overrides = [m.content for m in req.messages if m.role == "system"]
    user_msgs = [m.content for m in req.messages if m.role == "user"]
    if not user_msgs:
        raise HTTPException(400, "Falta al menos un mensaje de usuario.")

    sys_text = system_overrides[-1] if system_overrides else BASE_SYSTEM
    user_text = user_msgs[-1]

    chain = prompt | get_chat(model, req.temperature or 0.2)
    try:
        result = chain.invoke({"system": sys_text, "user": user_text})
        return ChatResponse(
            content=result.content,
            model=model,
            usage={"model": model}
        )
    except Exception as e:
        raise HTTPException(500, f"Error en generación: {e}")

@app.post("/embeddings", response_model=EmbeddingsResponse)
def embeddings(req: EmbeddingsRequest):
    model = ensure_model_allowed(req.model or DEFAULT_MODEL)
    if not req.input:
        raise HTTPException(400, "Lista de textos vacía.")
    try:
        embedder = get_embedder(model)
        vecs = embedder.embed_documents(req.input)
        return EmbeddingsResponse(embeddings=vecs, model=model)
    except Exception as e:
        raise HTTPException(500, f"Error generando embeddings: {e}")
