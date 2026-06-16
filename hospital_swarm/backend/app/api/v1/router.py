from fastapi import APIRouter
from app.api.v1.endpoints import (
    patients,
    agents,
    pheromones,
    simulation,
    metrics,
    graph,
    ws,
    tasks,
    journey,
    resources,
    patient_portal,
)

api_router = APIRouter()

api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(pheromones.router, prefix="/pheromones", tags=["pheromones"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(journey.router, prefix="/journey", tags=["journey"])
api_router.include_router(resources.router, prefix="/resources", tags=["resources"])
api_router.include_router(
    patient_portal.router, prefix="/patient-portal", tags=["patient-portal"]
)
