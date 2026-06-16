from typing import List, Optional, Dict, Any
from app.models.pheromone import Pheromone, PheromoneCreate, PheromoneUpdate, ACUITY_TIERS
from app.db.neo4j import run_query
from app.services.resource_tracker import ResourceTracker
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

NEXT_STEP = {
    "EMERGENCY": ("TRIAGED", "nurse"),
    "TRIAGED": ("DIAGNOSED", "doctor"),
    "DIAGNOSED": None,
    "LAB_REQUEST": None,
    "ICU_REQUEST": None,
    "PRESCRIPTION": None,
    "BED_READY": None,
    "TESTS_DONE": None,
    "LAB_COMPLETE": None,
    "MEDS_DISPENSED": None,
    "DISPATCHED": None,
    "DETERIORATION": ("TRIAGED", "nurse"),
    "ESCALATED": None,
    "CRITICAL_ESCALATION": None,
    "RESOURCE_SHORTAGE": None,
}

ROLE_TASKS = {
    "nurse": ["EMERGENCY", "DETERIORATION", "ESCALATED"],
    "doctor": ["TRIAGED", "LAB_COMPLETE", "ESCALATED", "CRITICAL_ESCALATION"],
    "icu": ["ICU_REQUEST", "RESOURCE_SHORTAGE"],
    "lab": ["LAB_REQUEST"],
    "pharmacy": ["PRESCRIPTION", "RESOURCE_SHORTAGE"],
    "ambulance": ["EMERGENCY", "RESOURCE_SHORTAGE"],
}

ROLE_ACTIONS = {
    "nurse": ("triage", "TRIAGED"),
    "doctor": ("diagnose", "DIAGNOSED"),
    "icu": ("prepare_bed", "BED_READY"),
    "lab": ("run_tests", "TESTS_DONE"),
    "pharmacy": ("dispense_meds", "MEDS_DISPENSED"),
    "ambulance": ("dispatch", "DISPATCHED"),
}

NOT_EXPIRED = "datetime(p.expires_at) > datetime()"


class PheromoneService:
    def __init__(self):
        self.resources = ResourceTracker()

    async def get_pheromones(self, skip: int = 0, limit: int = 100) -> List[Pheromone]:
        query = f"""
        MATCH (p:Pheromone)
        WHERE {NOT_EXPIRED} AND p.status = 'active'
        RETURN p
        ORDER BY p.strength DESC
        SKIP $skip
        LIMIT $limit
        """
        results = await run_query(query, {"skip": skip, "limit": limit})
        return [Pheromone(**record["p"]) for record in results]

    async def get_pheromones_by_type(self, types: List[str], skip: int = 0, limit: int = 100) -> List[Pheromone]:
        query = f"""
        MATCH (p:Pheromone)
        WHERE {NOT_EXPIRED} AND p.status = 'active' AND p.type IN $types
        RETURN p
        ORDER BY p.strength DESC
        SKIP $skip
        LIMIT $limit
        """
        results = await run_query(query, {"types": types, "skip": skip, "limit": limit})
        return [Pheromone(**record["p"]) for record in results]

    async def get_pheromones_for_patient(self, patient_id: str, limit: int = 50) -> List[Pheromone]:
        query = """
        MATCH (p:Pheromone {patient_id: $patient_id})
        RETURN p
        ORDER BY p.created_at DESC
        LIMIT $limit
        """
        results = await run_query(query, {"patient_id": patient_id, "limit": limit})
        return [Pheromone(**record["p"]) for record in results]

    async def create_pheromone(self, pheromone_in: PheromoneCreate) -> Pheromone:
        pheromone_id = f"PHR{str(uuid.uuid4().int)[:8]}"

        acuity_data = ACUITY_TIERS.get(pheromone_in.acuity or "", {})
        ttl = pheromone_in.ttl or acuity_data.get("ttl", 300)

        query = """
        CREATE (p:Pheromone {
            pheromone_id: $pheromone_id,
            type: $type,
            strength: $strength,
            ttl: $ttl,
            patient_id: $patient_id,
            status: $status,
            medication_name: $medication_name,
            medication_dosage: $medication_dosage,
            test_type: $test_type,
            test_result: $test_result,
            acuity: $acuity,
            escalated: $escalated,
            escalated_from: $escalated_from,
            sbar_situation: $sbar_situation,
            sbar_background: $sbar_background,
            sbar_assessment: $sbar_assessment,
            sbar_recommendation: $sbar_recommendation,
            vitals_hr: $vitals_hr,
            vitals_bp_systolic: $vitals_bp_systolic,
            vitals_bp_diastolic: $vitals_bp_diastolic,
            vitals_o2: $vitals_o2,
            vitals_temp: $vitals_temp,
            created_at: datetime(),
            expires_at: datetime() + duration({seconds: $ttl})
        })
        RETURN p
        """
        props = {
            "pheromone_id": pheromone_id,
            "type": pheromone_in.type,
            "strength": pheromone_in.strength,
            "ttl": ttl,
            "patient_id": pheromone_in.patient_id or "",
            "status": "active",
            "medication_name": pheromone_in.medication_name or "",
            "medication_dosage": pheromone_in.medication_dosage or "",
            "test_type": pheromone_in.test_type or "",
            "test_result": pheromone_in.test_result or "",
            "acuity": pheromone_in.acuity or "",
            "escalated": pheromone_in.escalated,
            "escalated_from": pheromone_in.escalated_from or "",
            "sbar_situation": pheromone_in.sbar_situation or "",
            "sbar_background": pheromone_in.sbar_background or "",
            "sbar_assessment": pheromone_in.sbar_assessment or "",
            "sbar_recommendation": pheromone_in.sbar_recommendation or "",
            "vitals_hr": pheromone_in.vitals_hr or 0,
            "vitals_bp_systolic": pheromone_in.vitals_bp_systolic or 0,
            "vitals_bp_diastolic": pheromone_in.vitals_bp_diastolic or 0,
            "vitals_o2": pheromone_in.vitals_o2 or 0,
            "vitals_temp": pheromone_in.vitals_temp or 0.0,
        }
        results = await run_query(query, props)
        return Pheromone(**results[0]["p"])

    async def get_pheromone_by_id(self, pheromone_id: str) -> Optional[Pheromone]:
        query = f"""
        MATCH (p:Pheromone {{pheromone_id: $pheromone_id}})
        WHERE {NOT_EXPIRED}
        RETURN p
        """
        results = await run_query(query, {"pheromone_id": pheromone_id})
        if not results:
            return None
        return Pheromone(**results[0]["p"])

    async def get_pheromone_by_id_any_status(self, pheromone_id: str) -> Optional[Pheromone]:
        query = """
        MATCH (p:Pheromone {pheromone_id: $pheromone_id})
        RETURN p
        """
        results = await run_query(query, {"pheromone_id": pheromone_id})
        if not results:
            return None
        return Pheromone(**results[0]["p"])

    async def update_pheromone(self, pheromone_id: str, pheromone_in: PheromoneUpdate) -> Optional[Pheromone]:
        existing = await self.get_pheromone_by_id_any_status(pheromone_id)
        if not existing:
            return None

        update_data = pheromone_in.model_dump(exclude_unset=True)
        if not update_data:
            return existing

        query = """
        MATCH (p:Pheromone {pheromone_id: $pheromone_id})
        SET p += $props
        RETURN p
        """
        results = await run_query(query, {"pheromone_id": pheromone_id, "props": update_data})
        return Pheromone(**results[0]["p"])

    async def expire_pheromone(self, pheromone_id: str) -> bool:
        query = """
        MATCH (p:Pheromone {pheromone_id: $pheromone_id})
        SET p.expires_at = datetime(), p.status = 'completed'
        RETURN count(p) as updated
        """
        results = await run_query(query, {"pheromone_id": pheromone_id})
        return results[0]["updated"] > 0

    async def complete_and_create_next(self, pheromone_id: str, role: str, next_type: str, **kwargs) -> Optional[Pheromone]:
        existing = await self.get_pheromone_by_id(pheromone_id)
        if not existing:
            return None

        if next_type:
            next_pheromone = PheromoneCreate(
                pheromone_id=f"PHR{str(uuid.uuid4().int)[:8]}",
                type=next_type,
                strength=existing.strength * 0.9,
                ttl=300,
                patient_id=existing.patient_id,
                status="active",
                **kwargs
            )
            created = await self.create_pheromone(next_pheromone)
            await self.expire_pheromone(pheromone_id)
            return created

        await self.expire_pheromone(pheromone_id)
        return None

    async def complete_and_create_multiple(self, pheromone_id: str, next_pheromones: List[PheromoneCreate]) -> List[Pheromone]:
        existing = await self.get_pheromone_by_id(pheromone_id)
        if not existing:
            return []

        created = []
        for p_in in next_pheromones:
            created.append(await self.create_pheromone(p_in))

        await self.expire_pheromone(pheromone_id)
        return created

    async def evaporate_pheromones(self, evaporation_rate: float = 0.1):
        query = f"""
        MATCH (p:Pheromone)
        WHERE {NOT_EXPIRED}
        SET p.strength = p.strength * (1 - $rate)
        RETURN count(p) as updated
        """
        results = await run_query(query, {"rate": evaporation_rate})
        return results[0]["updated"]

    async def diffuse_pheromones(self, diffusion_rate: float = 0.05):
        query = f"""
        MATCH (p:Pheromone)
        WHERE {NOT_EXPIRED}
        WITH p, rand() as r
        WHERE r < $rate
        SET p.strength = p.strength * 1.1
        RETURN count(p) as updated
        """
        results = await run_query(query, {"rate": diffusion_rate})
        return results[0]["updated"]

    async def get_stale_pheromones(self, max_age_seconds: int) -> List[Pheromone]:
        query = f"""
        MATCH (p:Pheromone)
        WHERE {NOT_EXPIRED} AND p.status = 'active'
          AND duration.between(p.created_at, datetime()).seconds > $max_age
          AND p.escalated = false
          AND p.type IN ['TRIAGED', 'DIAGNOSED', 'LAB_REQUEST', 'ICU_REQUEST', 'PRESCRIPTION']
        RETURN p
        """
        results = await run_query(query, {"max_age": max_age_seconds})
        return [Pheromone(**record["p"]) for record in results]

    async def get_escalated_pheromones(self) -> List[Pheromone]:
        query = f"""
        MATCH (p:Pheromone)
        WHERE {NOT_EXPIRED} AND p.status = 'active'
          AND p.type IN ['ESCALATED', 'CRITICAL_ESCALATION']
        RETURN p
        ORDER BY p.strength DESC
        """
        results = await run_query(query, {})
        return [Pheromone(**record["p"]) for record in results]

    def get_resource_status(self) -> Dict[str, Any]:
        return self.resources.get_status()

    def use_resource(self, name: str) -> bool:
        return self.resources.use_resource(name)

    def release_resource(self, name: str):
        self.resources.release_resource(name)

    async def check_resource_shortages(self) -> List[str]:
        return self.resources.check_shortages()
