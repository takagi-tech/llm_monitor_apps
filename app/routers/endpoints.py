from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from typing import List, Optional

import asyncio

from ..database import list_all, get_by_id, create, update, delete
from ..models import LLMEndpoint
from ..services.llm_detector import check_endpoint, get_model_name

router = APIRouter(prefix="/api/endpoints", tags=["endpoints"])

NETWORK_ORDER = ["AI2", "AI3"]
NETWORK_LABELS = {
    "AI2": "AI2：192.168.86",
    "AI3": "AI3：10.0.1",
}


def render_network_section(network: str, endpoints: List[LLMEndpoint]) -> str:
    if not endpoints:
        body = '<div class="network-empty">このネットワークには登録がありません</div>'
    else:
        body = "".join(
            f'''
            <div class="endpoint-item border-b p-4 flex items-center justify-between">
                <div class="flex-1">
                    <div class="font-semibold text-lg">{ep.name}</div>
                    <div class="text-gray-600">{ep.ip}:{ep.port}</div>
                    <div class="text-sm text-gray-500">モデル: {ep.model_name if ep.status == "online" and ep.model_name else "—"}</div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="status-badge {"status-online" if ep.status == "online" else "status-offline" if ep.status == "offline" else "status-unknown"}">{ep.status}</span>
                    <button class="btn btn-ping"
                            hx-post="/api/endpoints/{ep.id}/ping"
                            hx-target="#endpoint-content"
                            hx-swap="innerHTML">
                        更新
                    </button>
                    <button class="btn btn-delete"
                            hx-delete="/api/endpoints/{ep.id}"
                            hx-target="#endpoint-content"
                            hx-swap="innerHTML">
                        削除
                    </button>
                </div>
            </div>
            '''
            for ep in endpoints
        )

    return f'''
    <section class="network-group">
        <div class="network-header">
            <div class="network-title">{NETWORK_LABELS.get(network, network)}</div>
            <div class="network-count">{len(endpoints)} 台</div>
        </div>
        <div class="network-body">
            {body}
        </div>
    </section>
    '''


def render_endpoints_html(endpoints: List[LLMEndpoint]) -> str:
    if not endpoints:
        return '<div class="text-gray-500 p-4">LLMエンドポイントがありません</div>'
    grouped = {network: [] for network in NETWORK_ORDER}
    for ep in endpoints:
        if ep.network in grouped:
            grouped[ep.network].append(ep)
    return "".join(render_network_section(network, grouped[network]) for network in NETWORK_ORDER)

@router.get("")
async def list_endpoints(request: Request):
    endpoints = list_all()
    if request.headers.get("hx-request") == "true":
        return HTMLResponse(render_endpoints_html(endpoints))
    return endpoints


async def _refresh_all() -> List[LLMEndpoint]:
    """登録済み全マシンを並行してチェックし、状態とモデル名を更新する"""
    endpoints = list_all()
    results = await asyncio.gather(
        *(check_endpoint(ep.ip, ep.port) for ep in endpoints)
    )
    for ep, result in zip(endpoints, results):
        update(ep.id, status=result["status"], model_name=result["model_name"])
    return list_all()


@router.get("/refresh", response_class=HTMLResponse)
async def refresh_all():
    """自動ポーリング／手動更新の両方から呼ばれる。全台の稼働状況を最新化する。"""
    return HTMLResponse(render_endpoints_html(await _refresh_all()))

@router.post("")
async def create_endpoint(name: str = Form(...), network: str = Form(...), ip: str = Form(...), port: int = Form(...), api_key: str = Form(None)):
    ep = create(name, network, ip, port, api_key)
    # Auto-fetch model name on creation
    model_name = await get_model_name(ep.ip, ep.port)
    if model_name:
        update(ep.id, model_name=model_name)
    elif model_name is None:
        update(ep.id, model_name="現在、モデルは立っていません")
    endpoints = list_all()
    return HTMLResponse(render_endpoints_html(endpoints))

@router.get("/{endpoint_id}")
async def get_endpoint(endpoint_id: int):
    ep = get_by_id(endpoint_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return ep

@router.put("/{endpoint_id}")
async def update_endpoint(endpoint_id: int, data: LLMEndpoint):
    updated = update(endpoint_id, name=data.name, network=data.network, ip=data.ip, port=data.port, api_key=data.api_key)
    if not updated:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    # Auto-fetch model name on update
    model_name = await get_model_name(updated.ip, updated.port)
    if model_name:
        update(endpoint_id, model_name=model_name)
    elif model_name is None:
        update(endpoint_id, model_name="現在、モデルは立っていません")
    return get_by_id(endpoint_id)

@router.delete("/{endpoint_id}")
async def delete_endpoint(endpoint_id: int):
    if not delete(endpoint_id):
        raise HTTPException(status_code=404, detail="Endpoint not found")
    endpoints = list_all()
    return HTMLResponse(render_endpoints_html(endpoints))

@router.post("/{endpoint_id}/ping", response_class=HTMLResponse)
async def ping_endpoint(endpoint_id: int):
    ep = get_by_id(endpoint_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    result = await check_endpoint(ep.ip, ep.port)
    update(endpoint_id, status=result["status"], model_name=result["model_name"])
    endpoints = list_all()
    return HTMLResponse(render_endpoints_html(endpoints))


@router.post("/ping-all", response_class=HTMLResponse)
async def ping_all_endpoints():
    return HTMLResponse(render_endpoints_html(await _refresh_all()))

@router.get("/{endpoint_id}/model", response_class=HTMLResponse)
async def fetch_model(endpoint_id: int):
    ep = get_by_id(endpoint_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    model_name = await get_model_name(ep.ip, ep.port)
    if model_name:
        update(endpoint_id, model_name=model_name)
    endpoints = list_all()
    return HTMLResponse(render_endpoints_html(endpoints))
