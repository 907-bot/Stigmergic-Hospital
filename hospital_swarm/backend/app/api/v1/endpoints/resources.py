from fastapi import APIRouter
from typing import Dict, Any
from app.services.resource_tracker import ResourceTracker

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_resources():
    tracker = ResourceTracker()
    return tracker.get_status()
