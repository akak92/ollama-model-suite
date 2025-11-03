import os
from fastapi import HTTPException
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings

# Configuración desde variables de entorno
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://ollama:11434")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "llama3.1:latest")
ALLOWED_MODELS = [m.strip() for m in os.environ.get("ALLOWED_MODELS", "").split(",") if m.strip()]

BASE_SYSTEM = (
    "Respondé de forma técnica, clara y concisa. "
    "Si no sabés, decí 'No lo sé con certeza con el contexto dado'. "
    "Evitá inventar datos. Contesta siempre en idioma español."
)


def ensure_model_allowed(model: str) -> str:
    """Valida que el modelo esté permitido en la lista blanca."""
    if not model:
        model = DEFAULT_MODEL
    if ALLOWED_MODELS and model not in ALLOWED_MODELS:
        raise HTTPException(400, f"Modelo '{model}' no permitido. Permitidos: {ALLOWED_MODELS}")
    return model


def get_chat(model: str, temperature: float):
    """Crea una instancia de ChatOllama con la configuración especificada."""
    return ChatOllama(
        base_url=OLLAMA_BASE,
        model=model,
        temperature=temperature,
    )


def get_embedder(model: str):
    """Crea una instancia de OllamaEmbeddings para el modelo especificado."""
    return OllamaEmbeddings(
        base_url=OLLAMA_BASE,
        model=model,
    )