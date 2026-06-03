from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.manager import manager
import asyncio
import json
from app.services.simulation_service import SimulationService

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive and wait for any client messages (if needed)
            data = await websocket.receive_text()
            # Echo the message back or handle client commands
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)