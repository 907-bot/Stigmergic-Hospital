import asyncio
from neo4j import AsyncGraphDatabase
from app.core.config import settings
import logging
from datetime import datetime
import neo4j.time

logger = logging.getLogger(__name__)

_driver = None

def _convert_neo4j_value(value):
    if isinstance(value, neo4j.time.DateTime):
        return value.to_native()
    if isinstance(value, neo4j.time.Date):
        return datetime.combine(value.to_native(), datetime.min.time())
    if isinstance(value, neo4j.time.Time):
        return datetime.now().replace(hour=value.hour, minute=value.minute,
                                       second=value.second, microsecond=value.microsecond)
    if isinstance(value, dict):
        return {k: _convert_neo4j_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert_neo4j_value(v) for v in value]
    return value


def _record_to_dict(record):
    result = {}
    for key in record.keys():
        val = record[key]
        if hasattr(val, "items"):
            result[key] = {k: _convert_neo4j_value(v) for k, v in val.items()}
        else:
            result[key] = _convert_neo4j_value(val)
    return result


async def init_neo4j(max_retries: int = 10, retry_delay: float = 3.0):
    global _driver
    if _driver is not None:
        return _driver

    logger.info("Creating Neo4j driver singleton")
    _driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )

    last_error = None
    for attempt in range(max_retries):
        try:
            await _driver.verify_connectivity()
            logger.info("Neo4j driver verified and connected")
            return _driver
        except Exception as e:
            last_error = e
            logger.warning(f"Neo4j not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)

    logger.error(f"Failed to connect to Neo4j after {max_retries} attempts")
    raise last_error


async def close_neo4j():
    global _driver
    if _driver:
        logger.info("Closing Neo4j driver singleton")
        await _driver.close()
        _driver = None


def get_driver():
    global _driver
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized. Call init_neo4j() first.")
    return _driver


async def run_query(query: str, parameters: dict = None):
    driver = get_driver()
    async with driver.session() as session:
        try:
            result = await session.run(query, parameters or {})
            return [_record_to_dict(record) async for record in result]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise e


async def ensure_indexes():
    queries = [
        "CREATE INDEX IF NOT EXISTS FOR (p:Pheromone) ON (p.pheromone_id)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Pheromone) ON (p.patient_id)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Pheromone) ON (p.type)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Pheromone) ON (p.status)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Patient) ON (p.patient_id)",
        "CREATE INDEX IF NOT EXISTS FOR (a:Agent) ON (a.agent_id)",
    ]
    for q in queries:
        try:
            await run_query(q)
        except Exception as e:
            logger.warning(f"Index creation failed (may already exist): {e}")
    logger.info("Neo4j indexes ensured")
