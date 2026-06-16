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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None