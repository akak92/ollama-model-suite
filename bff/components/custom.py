"""
Endpoints personalizados de LangChain para el BFF
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
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

# Router personalizado
custom_router = APIRouter()

# Prompt template para LangChain
prompt = ChatPromptTemplate.from_messages([
    ("system", "{system}"),
    ("user", "{user}"),
])

@custom_router.get("/health", tags=["Custom"])
async def health():
    """Endpoint de salud del servicio"""
    return {"status": "ok", "default_model": DEFAULT_MODEL, "ollama_base": OLLAMA_BASE}

@custom_router.get("/models", tags=["Custom"])
async def list_models():
    """Lista modelos disponibles con formato personalizado"""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{OLLAMA_BASE}/api/tags")
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    data = r.json()
    tags = [item.get("name") for item in data.get("models", []) if item.get("name")]
    return {"models": tags, "allowed": ALLOWED_MODELS or "ANY"}

@custom_router.post("/pull", tags=["Custom"])
async def pull_model(req: PullRequest):
    """Descarga un modelo con formato personalizado"""
    payload = {"name": req.name}
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/pull", json=payload)
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return {"status": "ok", "pulled": req.name}

@custom_router.post("/chat", response_model=ChatResponse, tags=["Custom"])
def chat(req: ChatRequest):
    """Chat completion usando LangChain con BASE_SYSTEM automático"""
    model = ensure_model_allowed(req.model or DEFAULT_MODEL)

    user_msgs = [m.content for m in req.messages if m.role == "user"]
    if not user_msgs:
        raise HTTPException(400, "Falta al menos un mensaje de usuario.")

    # SIEMPRE usar BASE_SYSTEM (ignorar cualquier system message del usuario)
    sys_text = BASE_SYSTEM
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

@custom_router.post("/embeddings", response_model=EmbeddingsResponse, tags=["Custom"])
def embeddings(req: EmbeddingsRequest):
    """Genera embeddings usando LangChain"""
    model = ensure_model_allowed(req.model or DEFAULT_MODEL)
    if not req.input:
        raise HTTPException(400, "Lista de textos vacía.")
    try:
        embedder = get_embedder(model)
        vecs = embedder.embed_documents(req.input)
        return EmbeddingsResponse(embeddings=vecs, model=model)
    except Exception as e:
        raise HTTPException(500, f"Error generando embeddings: {e}")