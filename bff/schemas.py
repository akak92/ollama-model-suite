from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 512 

class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Dict[str, Any] = {}


class EmbeddingsRequest(BaseModel):
    input: List[str]
    model: Optional[str] = None


class EmbeddingsResponse(BaseModel):
    embeddings: List[List[float]]
    model: str


class PullRequest(BaseModel):
    name: str

