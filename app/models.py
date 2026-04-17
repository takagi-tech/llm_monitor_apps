from pydantic import BaseModel
from typing import Optional

class LLMEndpointCreate(BaseModel):
    name: str
    ip: str
    port: int
    api_key: Optional[str] = None

class LLMEndpointUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    api_key: Optional[str] = None

class LLMEndpoint(BaseModel):
    id: int
    name: str
    ip: str
    port: int
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    status: str = "unknown"
    created_at: str
    updated_at: str