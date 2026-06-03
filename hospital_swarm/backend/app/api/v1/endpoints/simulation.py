from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.services.simulation_service import SimulationService

router = APIRouter()

@router.post("/start", response_model=Dict[str, Any])
async def start_simulation(simulation_service: SimulationService = Depends()):
    return await simulation_service.start_simulation()

@router.post("/stop", response_model=Dict[str, Any])
async def stop_simulation(simulation_service: SimulationService = Depends()):
    return await simulation_service.stop_simulation()

@router.get("/status", response_model=Dict[str, Any])
async def get_simulation_status(simulation_service: SimulationService = Depends()):
    return await simulation_service.get_status()

@router.post("/reset", response_model=Dict[str, Any])
async def reset_simulation(simulation_service: SimulationService = Depends()):
    return await simulation_service.reset_simulation()

@router.post("/configure", response_model=Dict[str, Any])
async def configure_simulation(
    config: Dict[str, Any],
    simulation_service: SimulationService = Depends()
):
    return await simulation_service.configure(config)