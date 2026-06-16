from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_graph():
    return {"nodes": [], "edges": [], "message": "Graph endpoint"}
