from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models.pheromone import Pheromone, PheromoneCreate, PheromoneUpdate
from app.services.pheromone_service import PheromoneService

router = APIRouter()

@router.get("/", response_model=List[Pheromone])
async def list_pheromones(skip: int = 0, limit: int = 100, pheromone_service: PheromoneService = Depends()):
    return await pheromone_service.get_pheromones(skip=skip, limit=limit)

@router.post("/", response_model=Pheromone, status_code=status.HTTP_201_CREATED)
async def create_pheromone(pheromone_in: PheromoneCreate, pheromone_service: PheromoneService = Depends()):
    return await pheromone_service.create_pheromone(pheromone_in)

@router.get("/{pheromone_id}", response_model=Pheromone)
async def get_pheromone(pheromone_id: str, pheromone_service: PheromoneService = Depends()):
    pheromone = await pheromone_service.get_pheromone_by_id(pheromone_id)
    if not pheromone:
        raise HTTPException(status_code=404, detail="Pheromone not found")
    return pheromone

@router.put("/{pheromone_id}", response_model=Pheromone)
async def update_pheromone(
    pheromone_id: str, 
    pheromone_in: PheromoneUpdate, 
    pheromone_service: PheromoneService = Depends()
):
    pheromone = await pheromone_service.update_pheromone(pheromone_id, pheromone_in)
    if not pheromone:
        raise HTTPException(status_code=404, detail="Pheromone not found")
    return pheromone

@router.delete("/{pheromone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pheromone(pheromone_id: str, pheromone_service: PheromoneService = Depends()):
    success = await pheromone_service.delete_pheromone(pheromone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pheromone not found")
    return None