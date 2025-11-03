"""
Endpoints de proxy legacy/compatibilidad con API de Ollama
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import httpx
import json

from helpers import OLLAMA_BASE, BASE_SYSTEM

# Router de legacy/proxy
legacy_router = APIRouter(prefix="/api")

# === HELPER FUNCTIONS ===

def inject_base_system_to_messages(messages: list) -> list:
    """Inyecta BASE_SYSTEM SIEMPRE, reemplazando cualquier system message existente"""
    # Filtrar todos los system messages existentes
    non_system_messages = [msg for msg in messages if msg.get("role") != "system"]
    
    # Agregar BASE_SYSTEM al inicio SIEMPRE
    system_msg = {"role": "system", "content": BASE_SYSTEM}
    return [system_msg] + non_system_messages

def inject_base_system_to_prompt(prompt: str) -> str:
    """Inyecta BASE_SYSTEM SIEMPRE al prompt"""
    return f"{BASE_SYSTEM}\n\n{prompt}"

# === OLLAMA API COMPATIBILITY ENDPOINTS ===

@legacy_router.get("/version", tags=["Legacy"])
async def get_version():
    """Proxy endpoint para /api/version de Ollama"""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{OLLAMA_BASE}/api/version")
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@legacy_router.get("/tags", tags=["Legacy"])
async def get_tags():
    """Proxy endpoint para /api/tags de Ollama - lista todos los modelos"""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{OLLAMA_BASE}/api/tags")
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@legacy_router.post("/generate", tags=["Legacy"])
async def generate(request: Request):
    """Proxy endpoint para /api/generate de Ollama con inyección de BASE_SYSTEM"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # Inyectar BASE_SYSTEM en el prompt si es necesario
        if "prompt" in data:
            data["prompt"] = inject_base_system_to_prompt(data["prompt"])
        
        # Convertir de vuelta a JSON
        modified_body = json.dumps(data).encode('utf-8')
        
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(f"{OLLAMA_BASE}/api/generate", content=modified_body, 
                                 headers={"Content-Type": "application/json"})
        if r.status_code != 200:
            raise HTTPException(r.status_code, r.text)
        
        # Si es streaming, devolver el stream
        if r.headers.get("content-type") == "application/x-ndjson":
            return StreamingResponse(r.iter_bytes(), media_type="application/x-ndjson")
        else:
            return r.json()
            
    except json.JSONDecodeError:
        # Si no es JSON válido, hacer proxy directo
        body = await request.body()
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(f"{OLLAMA_BASE}/api/generate", content=body, 
                                 headers={"Content-Type": "application/json"})
        if r.status_code != 200:
            raise HTTPException(r.status_code, r.text)
        
        if r.headers.get("content-type") == "application/x-ndjson":
            return StreamingResponse(r.iter_bytes(), media_type="application/x-ndjson")
        else:
            return r.json()

@legacy_router.post("/chat", tags=["Legacy"])
async def ollama_chat(request: Request):
    """Proxy endpoint para /api/chat de Ollama con inyección de BASE_SYSTEM"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # Inyectar BASE_SYSTEM en los mensajes si es necesario
        if "messages" in data:
            data["messages"] = inject_base_system_to_messages(data["messages"])
        
        # Convertir de vuelta a JSON
        modified_body = json.dumps(data).encode('utf-8')
        
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(f"{OLLAMA_BASE}/api/chat", content=modified_body,
                                 headers={"Content-Type": "application/json"})
        if r.status_code != 200:
            raise HTTPException(r.status_code, r.text)
        
        # Si es streaming, devolver el stream
        if r.headers.get("content-type") == "application/x-ndjson":
            return StreamingResponse(r.iter_bytes(), media_type="application/x-ndjson")
        else:
            return r.json()
            
    except json.JSONDecodeError:
        # Si no es JSON válido, hacer proxy directo
        body = await request.body()
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(f"{OLLAMA_BASE}/api/chat", content=body,
                                 headers={"Content-Type": "application/json"})
        if r.status_code != 200:
            raise HTTPException(r.status_code, r.text)
        
        if r.headers.get("content-type") == "application/x-ndjson":
            return StreamingResponse(r.iter_bytes(), media_type="application/x-ndjson")
        else:
            return r.json()

@legacy_router.post("/pull", tags=["Legacy"])
async def ollama_pull(request: Request):
    """Proxy endpoint para /api/pull de Ollama"""
    body = await request.body()
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/pull", content=body,
                             headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    
    # Si es streaming, devolver el stream  
    if r.headers.get("content-type") == "application/x-ndjson":
        return StreamingResponse(r.iter_bytes(), media_type="application/x-ndjson")
    else:
        return r.json()

@legacy_router.post("/push", tags=["Legacy"])
async def ollama_push(request: Request):
    """Proxy endpoint para /api/push de Ollama"""
    body = await request.body()
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/push", content=body,
                             headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    
    if r.headers.get("content-type") == "application/x-ndjson":
        return StreamingResponse(r.iter_bytes(), media_type="application/x-ndjson")
    else:
        return r.json()

@legacy_router.post("/create", tags=["Legacy"])
async def ollama_create(request: Request):
    """Proxy endpoint para /api/create de Ollama"""
    body = await request.body()
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/create", content=body,
                             headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    
    if r.headers.get("content-type") == "application/x-ndjson":
        return StreamingResponse(r.iter_bytes(), media_type="application/x-ndjson")
    else:
        return r.json()

@legacy_router.delete("/delete", tags=["Legacy"])
async def ollama_delete(request: Request):
    """Proxy endpoint para /api/delete de Ollama"""
    body = await request.body()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.delete(f"{OLLAMA_BASE}/api/delete", content=body,
                               headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@legacy_router.post("/copy", tags=["Legacy"])
async def ollama_copy(request: Request):
    """Proxy endpoint para /api/copy de Ollama"""
    body = await request.body()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/copy", content=body,
                             headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@legacy_router.post("/show", tags=["Legacy"])
async def ollama_show(request: Request):
    """Proxy endpoint para /api/show de Ollama"""
    body = await request.body()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/show", content=body,
                             headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@legacy_router.post("/embeddings", tags=["Legacy"])
async def ollama_embeddings(request: Request):
    """Proxy endpoint para /api/embeddings de Ollama"""
    body = await request.body()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{OLLAMA_BASE}/api/embeddings", content=body,
                             headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)
    return r.json()