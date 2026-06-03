from typing import List, Optional, Dict, Any
from app.db.neo4j import Neo4jService
import logging

logger = logging.getLogger(__name__)

class HospitalService:
    def __init__(self, neo4j_service: Neo4jService = None):
        self.neo4j_service = neo4j_service or Neo4jService()

    async def initialize_hospital(self):
        """Initialize hospital infrastructure: rooms, equipment, medication nodes."""
        try:
            # Create room nodes
            rooms = [
                {"room_id": "ER01", "type": "ER", "capacity": 10},
                {"room_id": "ICU01", "type": "ICU", "capacity": 5},
                {"room_id": "WARD_A01", "type": "Ward A", "capacity": 20},
                {"room_id": "WARD_B01", "type": "Ward B", "capacity": 20},
                {"room_id": "LAB01", "type": "Lab", "capacity": 15},
                {"room_id": "PHARM01", "type": "Pharmacy", "capacity": 10},
            ]
            for room in rooms:
                query = """
                MERGE (r:Room {room_id: $room_id})
                SET r.type = $type, r.capacity = $capacity
                """
                await self.neo4j_service.run_query(query, room)

            # Create equipment nodes (simplified)
            equipment = [
                {"equipment_id": "VENT01", "type": "Ventilator", "status": "available"},
                {"equipment_id": "MONITOR01", "type": "Monitor", "status": "available"},
                {"equipment_id": "DEFIB01", "type": "Defibrillator", "status": "available"},
            ]
            for equip in equipment:
                query = """
                MERGE (e:Equipment {equipment_id: $equipment_id})
                SET e.type = $type, e.status = $status
                """
                await self.neo4j_service.run_query(query, equip)

            # Create medication nodes (simplified)
            medications = [
                {"medication_id": "ASPIRIN01", "name": "Aspirin", "dosage": "325mg"},
                {"medication_id": "HEPARIN01", "name": "Heparin", "dosage": "1000u"},
                {"medication_id": "OXYGEN01", "name": "Oxygen", "dosage": "2L/min"},
            ]
            for med in medications:
                query = """
                MERGE (m:Medication {medication_id: $medication_id})
                SET m.name = $name, m.dosage = $dosage
                """
                await self.neo4j_service.run_query(query, med)

            logger.info("Hospital infrastructure initialized")
        except Exception as e:
            logger.error(f"Error initializing hospital infrastructure: {e}")
            raise e

    async def assign_patient_to_room(self, patient_id: str, room_id: str) -> bool:
        """Assign a patient to a room."""
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            MATCH (r:Room {room_id: $room_id})
            MERGE (p)-[rel:LOCATED_IN]->(r)
            SET rel.assigned_at = datetime()
            RETURN count(rel) as assigned
            """
            results = await self.neo4j_service.run_query(query, {"patient_id": patient_id, "room_id": room_id})
            return results[0]["assigned"] > 0
        except Exception as e:
            logger.error(f"Error assigning patient {patient_id} to room {room_id}: {e}")
            return False

    async def assign_patient_to_agent(self, patient_id: str, agent_id: str, relationship_type: str = "ASSIGNED_TO") -> bool:
        """Assign a patient to an agent (nurse, doctor, etc.)."""
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            MATCH (a:Agent {agent_id: $agent_id})
            MERGE (p)-[rel:%s]->(a)
            SET rel.assigned_at = datetime()
            RETURN count(rel) as assigned
            """ % relationship_type
            results = await self.neo4j_service.run_query(query, {"patient_id": patient_id, "agent_id": agent_id})
            return results[0]["assigned"] > 0
        except Exception as e:
            logger.error(f"Error assigning patient {patient_id} to agent {agent_id}: {e}")
            return False

    async def update_patient_status(self, patient_id: str, status: str) -> bool:
        """Update the status of a patient."""
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            SET p.status = $status
            RETURN count(p) as updated
            """
            results = await self.neo4j_service.run_query(query, {"patient_id": patient_id, "status": status})
            return results[0]["updated"] > 0
        except Exception as e:
            logger.error(f"Error updating patient {patient_id} status to {status}: {e}")
            return False

    async def get_patient_location(self, patient_id: str) -> Optional[str]:
        """Get the current room location of a patient."""
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:LOCATED_IN]->(r:Room)
            RETURN r.room_id as room_id
            """
            results = await self.neo4j_service.run_query(query, {"patient_id": patient_id})
            if results:
                return results[0]["room_id"]
            return None
        except Exception as e:
            logger.error(f"Error getting location for patient {patient_id}: {e}")
            return None

    async def get_room_occupancy(self, room_id: str) -> Dict[str, Any]:
        """Get the current occupancy and capacity of a room."""
        try:
            query = """
            MATCH (r:Room {room_id: $room_id})
            OPTIONAL MATCH (p:Patient)-[:LOCATED_IN]->(r)
            RETURN r.capacity as capacity, count(p) as current_occupancy
            """
            results = await self.neo4j_service.run_query(query, {"room_id": room_id})
            if results:
                return {
                    "capacity": results[0]["capacity"],
                    "current_occupancy": results[0]["current_occupancy"],
                    "occupancy_rate": results[0]["current_occupancy"] / results[0]["capacity"] if results[0]["capacity"] > 0 else 0
                }
            return {"capacity": 0, "current_occupancy": 0, "occupancy_rate": 0}
        except Exception as e:
            logger.error(f"Error getting occupancy for room {room_id}: {e}")
            return {"capacity": 0, "current_occupancy": 0, "occupancy_rate": 0}

    async def get_hospital_state(self) -> Dict[str, Any]:
        """Get the overall state of the hospital for the dashboard."""
        try:
            # Get room occupancies
            rooms = ["ER01", "ICU01", "WARD_A01", "WARD_B01", "LAB01", "PHARM01"]
            room_states = {}
            for room in rooms:
                room_states[room] = await self.get_room_occupancy(room)

            # Get patient counts by status
            query = """
            MATCH (p:Patient)
            RETURN p.status as status, count(p) as count
            """
            patient_status_counts = {}
            results = await self.neo4j_service.run_query(query)
            for record in results:
                patient_status_counts[record["status"]] = record["count"]

            # Get agent counts by status
            query = """
            MATCH (a:Agent)
            RETURN a.status as status, count(a) as count
            """
            agent_status_counts = {}
            results = await self.neo4j_service.run_query(query)
            for record in results:
                agent_status_counts[record["status"]] = record["count"]

            return {
                "rooms": room_states,
                "patient_status_counts": patient_status_counts,
                "agent_status_counts": agent_status_counts
            }
        except Exception as e:
            logger.error(f"Error getting hospital state: {e}")
            return {"rooms": {}, "patient_status_counts": {}, "agent_status_counts": {}}

# Dependency to get HospitalService
async def get_hospital_service():
    service = HospitalService()
    # Note: We are not initializing the hospital here because we don't want to do it on every request.
    # Instead, we will initialize it once when the simulation starts.
    return service