from typing import List, Optional
from app.models.patient import Patient, PatientCreate, PatientUpdate
from app.db.neo4j import Neo4jService

class PatientService:
    def __init__(self, neo4j_service: Neo4jService = None):
        self.neo4j_service = neo4j_service or Neo4jService()

    async def get_patients(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        query = """
        MATCH (p:Patient)
        RETURN p
        SKIP $skip
        LIMIT $limit
        """
        results = await self.neo4j_service.run_query(query, {"skip": skip, "limit": limit})
        return [Patient(**record["p"]) for record in results]

    async def create_patient(self, patient_in: PatientCreate) -> Patient:
        query = """
        CREATE (p:Patient $props)
        RETURN p
        """
        props = patient_in.dict()
        results = await self.neo4j_service.run_query(query, {"props": props})
        return Patient(**results[0]["p"])

    async def get_patient_by_id(self, patient_id: str) -> Optional[Patient]:
        query = """
        MATCH (p:Patient {patient_id: $patient_id})
        RETURN p
        """
        results = await self.neo4j_service.run_query(query, {"patient_id": patient_id})
        if not results:
            return None
        return Patient(**results[0]["p"])

    async def get_waiting_patients(self, limit: int = 100) -> List[Patient]:
        query = """
        MATCH (p:Patient {status: "waiting"})
        RETURN p
        LIMIT $limit
        """
        results = await self.neo4j_service.run_query(query, {"limit": limit})
        return [Patient(**record["p"]) for record in results]

    async def update_patient(self, patient_id: str, patient_in: PatientUpdate) -> Optional[Patient]:
        # First, check if the patient exists
        existing = await self.get_patient_by_id(patient_id)
        if not existing:
            return None

        # Update the patient
        update_data = patient_in.dict(exclude_unset=True)
        if not update_data:
            return existing

        query = """
        MATCH (p:Patient {patient_id: $patient_id})
        SET p += $props
        RETURN p
        """
        results = await self.neo4j_service.run_query(
            query, 
            {"patient_id": patient_id, "props": update_data}
        )
        return Patient(**results[0]["p"])

    async def delete_patient(self, patient_id: str) -> bool:
        query = """
        MATCH (p:Patient {patient_id: $patient_id})
        DELETE p
        RETURN count(p) as deleted
        """
        results = await self.neo4j_service.run_query(query, {"patient_id": patient_id})
        return results[0]["deleted"] > 0