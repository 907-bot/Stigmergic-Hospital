from typing import List, Optional
from app.models.agent import Agent, AgentCreate, AgentUpdate
from app.models.pheromone import Pheromone
from app.db.neo4j import run_query
import logging

logger = logging.getLogger(__name__)


class AgentService:
    async def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        query = """
        MATCH (a:Agent)
        RETURN a
        SKIP $skip
        LIMIT $limit
        """
        results = await run_query(query, {"skip": skip, "limit": limit})
        return [Agent(**record["a"]) for record in results]

    async def create_agent(self, agent_in: AgentCreate) -> Agent:
        query = """
        CREATE (a:Agent $props)
        RETURN a
        """
        props = agent_in.model_dump()
        results = await run_query(query, {"props": props})
        return Agent(**results[0]["a"])

    async def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        query = """
        MATCH (a:Agent {agent_id: $agent_id})
        RETURN a
        """
        results = await run_query(query, {"agent_id": agent_id})
        if not results:
            return None
        return Agent(**results[0]["a"])

    async def update_agent(self, agent_id: str, agent_in: AgentUpdate) -> Optional[Agent]:
        existing = await self.get_agent_by_id(agent_id)
        if not existing:
            return None

        update_data = agent_in.model_dump(exclude_unset=True)
        if not update_data:
            return existing

        query = """
        MATCH (a:Agent {agent_id: $agent_id})
        SET a += $props
        RETURN a
        """
        results = await run_query(query, {"agent_id": agent_id, "props": update_data})
        return Agent(**results[0]["a"])

    async def delete_agent(self, agent_id: str) -> bool:
        query = """
        MATCH (a:Agent {agent_id: $agent_id})
        DELETE a
        RETURN count(a) as deleted
        """
        results = await run_query(query, {"agent_id": agent_id})
        return results[0]["deleted"] > 0

    async def decide_actions(self, agents: List[Agent], pheromones: List[Pheromone]) -> List[str]:
        actions = []
        for agent in agents:
            try:
                action = self._decide_agent_action(agent, pheromones)
                if action:
                    actions.append(action)
                    logger.debug(f"Agent {agent.agent_id} ({agent.role}) decided action: {action}")
            except Exception as e:
                logger.error(f"Error deciding action for agent {agent.agent_id}: {e}")
        return actions

    def _decide_agent_action(self, agent: Agent, pheromones: List[Pheromone]) -> Optional[str]:
        active_pheromones = pheromones

        if agent.role == "nurse":
            emergency_pheromones = [p for p in active_pheromones if p.type == "EMERGENCY" and p.strength > 0.6]
            if emergency_pheromones:
                strongest = max(emergency_pheromones, key=lambda p: p.strength)
                return f"Nurse {agent.agent_id} triaged patient (emergency strength: {strongest.strength:.2f})"

        elif agent.role == "doctor":
            emergency_pheromones = [p for p in active_pheromones if p.type == "EMERGENCY" and p.strength > 0.7]
            if emergency_pheromones:
                strongest = max(emergency_pheromones, key=lambda p: p.strength)
                return f"Doctor {agent.agent_id} diagnosed patient (emergency strength: {strongest.strength:.2f})"

        elif agent.role == "icu":
            emergency_pheromones = [p for p in active_pheromones if p.type == "EMERGENCY" and p.strength > 0.8]
            if emergency_pheromones:
                strongest = max(emergency_pheromones, key=lambda p: p.strength)
                return f"ICU {agent.agent_id} prepared bed (emergency strength: {strongest.strength:.2f})"

        elif agent.role == "lab":
            emergency_pheromones = [p for p in active_pheromones if p.type == "EMERGENCY" and p.strength > 0.65]
            if emergency_pheromones:
                strongest = max(emergency_pheromones, key=lambda p: p.strength)
                return f"Lab {agent.agent_id} scheduled tests (emergency strength: {strongest.strength:.2f})"

        elif agent.role == "pharmacy":
            emergency_pheromones = [p for p in active_pheromones if p.type == "EMERGENCY" and p.strength > 0.7]
            if emergency_pheromones:
                strongest = max(emergency_pheromones, key=lambda p: p.strength)
                return f"Pharmacy {agent.agent_id} prepared medications (emergency strength: {strongest.strength:.2f})"

        elif agent.role == "ambulance":
            emergency_pheromones = [p for p in active_pheromones if p.type == "EMERGENCY" and p.strength > 0.75]
            if emergency_pheromones:
                strongest = max(emergency_pheromones, key=lambda p: p.strength)
                return f"Ambulance {agent.agent_id} dispatched (emergency strength: {strongest.strength:.2f})"

        return None
