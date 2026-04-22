# Database layer - using JSON storage
import json
from pathlib import Path
from typing import List, Optional
from .models import LLMEndpoint
from datetime import datetime

STORAGE_PATH = Path(__file__).parent.parent / "endpoints.json"

def _load_raw() -> List[dict]:
    if not STORAGE_PATH.exists():
        return []
    with open(STORAGE_PATH) as f:
        return json.load(f)

def _save_raw(data: List[dict]):
    with open(STORAGE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get_next_id() -> int:
    data = _load_raw()
    if not data:
        return 1
    return max(item["id"] for item in data) + 1

def list_all() -> List[LLMEndpoint]:
    return [LLMEndpoint(**item) for item in _load_raw()]

def get_by_id(endpoint_id: int) -> Optional[LLMEndpoint]:
    data = _load_raw()
    for item in data:
        if item["id"] == endpoint_id:
            return LLMEndpoint(**item)
    return None

def create(name: str, network: str, ip: str, port: int, api_key: Optional[str] = None) -> LLMEndpoint:
    data = _load_raw()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_ep = LLMEndpoint(
        id=get_next_id(),
        name=name,
        network=network,
        ip=ip,
        port=port,
        api_key=api_key,
        model_name=None,
        status="unknown",
        created_at=now,
        updated_at=now,
    )
    data.append(new_ep.dict())
    _save_raw(data)
    return new_ep

def update(endpoint_id: int, name: Optional[str] = None, network: Optional[str] = None, ip: Optional[str] = None,
           port: Optional[int] = None, api_key: Optional[str] = None,
           model_name: Optional[str] = None, status: Optional[str] = None) -> Optional[LLMEndpoint]:
    data = _load_raw()
    for i, item in enumerate(data):
        if item["id"] == endpoint_id:
            if name is not None:
                item["name"] = name
            if network is not None:
                item["network"] = network
            if ip is not None:
                item["ip"] = ip
            if port is not None:
                item["port"] = port
            if api_key is not None:
                item["api_key"] = api_key
            if model_name is not None:
                item["model_name"] = model_name
            if status is not None:
                item["status"] = status
            item["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data[i] = item
            _save_raw(data)
            return LLMEndpoint(**item)
    return None

def delete(endpoint_id: int) -> bool:
    data = _load_raw()
    original_len = len(data)
    data = [item for item in data if item["id"] != endpoint_id]
    if len(data) < original_len:
        _save_raw(data)
        return True
    return False
