from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AgentBase(BaseModel):
    agent_id: str = Field(..., example="DOC01")
    role: str = Field(..., example="doctor")
    status: str = Field(..., example="available")

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None

class Agent(AgentBase):
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True