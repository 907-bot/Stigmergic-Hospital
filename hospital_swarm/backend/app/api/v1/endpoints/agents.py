from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models.agent import Agent, AgentCreate, AgentUpdate
from app.services.agent_service import AgentService

router = APIRouter()

@router.get("/", response_model=List[Agent])
async def list_agents(skip: int = 0, limit: int = 100, agent_service: AgentService = Depends()):
    return await agent_service.get_agents(skip=skip, limit=limit)

@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_in: AgentCreate, agent_service: AgentService = Depends()):
    return await agent_service.create_agent(agent_in)

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, agent_service: AgentService = Depends()):
    agent = await agent_service.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str, 
    agent_in: AgentUpdate, 
    agent_service: AgentService = Depends()
):
    agent = await agent_service.update_agent(agent_id, agent_in)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, agent_service: AgentService = Depends()):
    success = await agent_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None