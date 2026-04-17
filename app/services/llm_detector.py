import httpx
from typing import Optional

async def check_status(ip: str, port: int) -> bool:
    """LLMのヘルスチェックを行う"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{ip}:{port}/health")
            return response.status_code == 200
    except Exception:
        return False

async def get_model_name(ip: str, port: int) -> Optional[str]:
    """vllm/sglang/llama.cppからモデル名を取得する"""
    endpoints = [
        f"http://{ip}:{port}/v1/models",
        f"http://{ip}:{port}/props",
    ]
    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in endpoints:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if "/v1/models" in url:
                        models = data.get("data", [])
                        if models:
                            return models[0].get("id", "unknown")
                    elif "/props" in url:
                        return data.get("model_name", "unknown")
            except Exception:
                continue
    return None