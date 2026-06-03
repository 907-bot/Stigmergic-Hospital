from neo4j import AsyncGraphDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self):
        self.driver = None

    async def connect(self):
        """Create driver instance"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Verify connection
            await self.driver.verify_connectivity()
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise e

    async def close(self):
        """Close driver instance"""
        if self.driver:
            await self.driver.close()
            logger.info("Disconnected from Neo4j")

    async def run_query(self, query: str, parameters: dict = None):
        """Run a Cypher query and return results"""
        if not self.driver:
            await self.connect()
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, parameters or {})
                # Convert to list of dictionaries
                return [dict(record) async for record in result]
            except Exception as e:
                logger.error(f"Query failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Parameters: {parameters}")
                raise e

# Dependency to get Neo4j service
async def get_neo4j_service():
    service = Neo4jService()
    await service.connect()
    try:
        yield service
    finally:
        await service.close()