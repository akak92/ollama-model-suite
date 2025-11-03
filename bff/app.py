from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Importar los routers de componentes
from components.custom import custom_router
from components.legacy import legacy_router

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

# === ROUTERS ===

# Incluir router de endpoints personalizados (sin prefijo)
app.include_router(custom_router)

# Incluir router de endpoints legacy/proxy (con prefijo /api)
app.include_router(legacy_router)
