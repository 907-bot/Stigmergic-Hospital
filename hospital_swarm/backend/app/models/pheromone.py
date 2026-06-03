from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PheromoneBase(BaseModel):
    pheromone_id: str = Field(..., example="PHR001")
    type: str = Field(..., example="EMERGENCY")
    strength: float = Field(..., ge=0.0, le=1.0, example=0.95)
    ttl: int = Field(..., example=300)  # time to live in seconds
    expires_at: Optional[datetime] = Field(None, example="2024-06-02T12:00:00Z")

class PheromoneCreate(PheromoneBase):
    pass

class PheromoneUpdate(BaseModel):
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    ttl: Optional[int] = None

class Pheromone(PheromoneBase):
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True