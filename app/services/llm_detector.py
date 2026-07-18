import httpx
from typing import Optional

# オフラインのマシンで長く待たされないよう短めに設定
TIMEOUT = 3.0

async def get_model_name(ip: str, port: int) -> Optional[str]:
    """vllm/sglang/llama.cppからモデル名を取得する"""
    endpoints = [
        f"http://{ip}:{port}/v1/models",
        f"http://{ip}:{port}/props",
    ]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
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

async def check_status(ip: str, port: int) -> bool:
    """（後方互換）/health による生死確認"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"http://{ip}:{port}/health")
            return response.status_code == 200
    except Exception:
        return False

async def check_endpoint(ip: str, port: int) -> dict:
    """マシンの稼働状況を確認する。

    /v1/models（→/props）でモデル名が取れれば online + モデル名、
    取れなければ offline とする。
    「モデルが立っている ⟹ サーバーは起動している」ため、
    これ一本で「生きているか」「何が立っているか」を同時に判定できる。
    """
    model_name = await get_model_name(ip, port)
    if model_name:
        return {"status": "online", "model_name": model_name}
    return {"status": "offline", "model_name": ""}
