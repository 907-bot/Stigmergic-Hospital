from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.simulation_service import SimulationService

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_metrics(simulation_service: SimulationService = Depends()):
    status = await simulation_service.get_status()
    # In a real implementation, we would compute more detailed metrics
    return {
        "simulation": status,
        "performance": {
            "signal_reachability": 0.95,  # Placeholder
            "average_reaction_time_ms": 45,  # Placeholder
            "throughput_patients_per_hour": 120,  # Placeholder
            "resource_utilization": {
                "beds": 0.65,
                "staff": 0.70,
                "labs": 0.45
            }
        }
    }