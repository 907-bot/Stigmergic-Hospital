from typing import List, Optional
from app.models.pheromone import Pheromone, PheromoneCreate, PheromoneUpdate
from app.db.neo4j import Neo4jService
import uuid
from datetime import datetime, timedelta

class PheromoneService:
    def __init__(self, neo4j_service: Neo4jService = None):
        self.neo4j_service = neo4j_service or Neo4jService()

    async def get_pheromones(self, skip: int = 0, limit: int = 100) -> List[Pheromone]:
        query = """
        MATCH (p:Pheromone)
        WHERE p.expires_at > datetime()
        RETURN p
        SKIP $skip
        LIMIT $limit
        """
        results = await self.neo4j_service.run_query(query, {"skip": skip, "limit": limit})
        return [Pheromone(**record["p"]) for record in results]

    async def create_pheromone(self, pheromone_in: PheromoneCreate) -> Pheromone:
        # Generate a unique ID if not provided
        pheromone_id = f"PHR{str(uuid.uuid4().int)[:8]}"
        # Calculate expiration time based on TTL
        expires_at = datetime.now() + timedelta(seconds=pheromone_in.ttl)
        
        query = """
        CREATE (p:Pheromone {
            pheromone_id: $pheromone_id,
            type: $type,
            strength: $strength,
            ttl: $ttl,
            created_at: datetime(),
            expires_at: $expires_at
        })
        RETURN p
        """
        props = {
            "pheromone_id": pheromone_id,
            "type": pheromone_in.type,
            "strength": pheromone_in.strength,
            "ttl": pheromone_in.ttl,
            "expires_at": expires_at.isoformat()
        }
        results = await self.neo4j_service.run_query(query, props)
        return Pheromone(**results[0]["p"])

    async def get_pheromone_by_id(self, pheromone_id: str) -> Optional[Pheromone]:
        query = """
        MATCH (p:Pheromone {pheromone_id: $pheromone_id})
        WHERE p.expires_at > datetime()
        RETURN p
        """
        results = await self.neo4j_service.run_query(query, {"pheromone_id": pheromone_id})
        if not results:
            return None
        return Pheromone(**results[0]["p"])

    async def update_pheromone(self, pheromone_id: str, pheromone_in: PheromoneUpdate) -> Optional[Pheromone]:
        # First, check if the pheromone exists and is not expired
        existing = await self.get_pheromone_by_id(pheromone_id)
        if not existing:
            return None

        # Update the pheromone
        update_data = pheromone_in.dict(exclude_unset=True)
        if not update_data:
            return existing

        # Recalculate expiration if TTL is updated
        if "ttl" in update_data:
            # We don't have the original creation time, so we'll assume we update from now
            # In a more complete implementation, we would store the creation time
            update_data["expires_at"] = (datetime.now() + timedelta(seconds=update_data["ttl"])).isoformat()
            # Remove ttl from update_data because we are storing expires_at
            del update_data["ttl"]

        query = """
        MATCH (p:Pheromone {pheromone_id: $pheromone_id})
        SET p += $props
        RETURN p
        """
        results = await self.neo4j_service.run_query(
            query, 
            {"pheromone_id": pheromone_id, "props": update_data}
        )
        return Pheromone(**results[0]["p"])

    async def delete_pheromone(self, pheromone_id: str) -> bool:
        # In our case, deleting means expiring immediately
        query = """
        MATCH (p:Pheromone {pheromone_id: $pheromone_id})
        SET p.expires_at = datetime()
        RETURN count(p) as updated
        """
        results = await self.neo4j_service.run_query(query, {"pheromone_id": pheromone_id})
        return results[0]["updated"] > 0

    async def evaporate_pheromones(self, evaporation_rate: float = 0.1):
        """Reduce the strength of all pheromones by evaporation_rate"""
        query = """
        MATCH (p:Pheromone)
        WHERE p.expires_at > datetime()
        SET p.strength = p.strength * (1 - $rate)
        RETURN count(p) as updated
        """
        results = await self.neo4j_service.run_query(query, {"rate": evaporation_rate})
        return results[0]["updated"]

    async def diffuse_pheromones(self, diffusion_rate: float = 0.05):
        """Simulate diffusion by slightly increasing strength of nearby pheromones (simplified)"""
        # In a real implementation, we would consider proximity in the graph
        # For now, we'll just do a global boost to a random subset to simulate diffusion
        query = """
        MATCH (p:Pheromone)
        WHERE p.expires_at > datetime()
        WITH p, rand() as r
        WHERE r < $rate
        SET p.strength = p.strength * 1.1
        RETURN count(p) as updated
        """
        results = await self.neo4j_service.run_query(query, {"rate": diffusion_rate})
        return results[0]["updated"]