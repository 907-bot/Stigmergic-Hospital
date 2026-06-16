from typing import List, Optional, Dict, Any
from app.db.neo4j import run_query
import logging

logger = logging.getLogger(__name__)


class HospitalService:
    async def initialize_hospital(self):
        try:
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
                await run_query(query, room)

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
                await run_query(query, equip)

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
                await run_query(query, med)

            logger.info("Hospital infrastructure initialized")
        except Exception as e:
            logger.error(f"Error initializing hospital infrastructure: {e}")
            raise e

    async def assign_patient_to_room(self, patient_id: str, room_id: str) -> bool:
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            MATCH (r:Room {room_id: $room_id})
            MERGE (p)-[rel:LOCATED_IN]->(r)
            SET rel.assigned_at = datetime()
            RETURN count(rel) as assigned
            """
            results = await run_query(query, {"patient_id": patient_id, "room_id": room_id})
            return results[0]["assigned"] > 0
        except Exception as e:
            logger.error(f"Error assigning patient {patient_id} to room {room_id}: {e}")
            return False

    async def assign_patient_to_agent(self, patient_id: str, agent_id: str, relationship_type: str = "ASSIGNED_TO") -> bool:
        try:
            query = f"""
            MATCH (p:Patient {{patient_id: $patient_id}})
            MATCH (a:Agent {{agent_id: $agent_id}})
            MERGE (p)-[rel:{relationship_type}]->(a)
            SET rel.assigned_at = datetime()
            RETURN count(rel) as assigned
            """
            results = await run_query(query, {"patient_id": patient_id, "agent_id": agent_id})
            return results[0]["assigned"] > 0
        except Exception as e:
            logger.error(f"Error assigning patient {patient_id} to agent {agent_id}: {e}")
            return False

    async def update_patient_status(self, patient_id: str, status: str) -> bool:
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            SET p.status = $status
            RETURN count(p) as updated
            """
            results = await run_query(query, {"patient_id": patient_id, "status": status})
            return results[0]["updated"] > 0
        except Exception as e:
            logger.error(f"Error updating patient {patient_id} status to {status}: {e}")
            return False

    async def get_patient_location(self, patient_id: str) -> Optional[str]:
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:LOCATED_IN]->(r:Room)
            RETURN r.room_id as room_id
            """
            results = await run_query(query, {"patient_id": patient_id})
            if results:
                return results[0]["room_id"]
            return None
        except Exception as e:
            logger.error(f"Error getting location for patient {patient_id}: {e}")
            return None

    async def get_room_occupancy(self, room_id: str) -> Dict[str, Any]:
        try:
            query = """
            MATCH (r:Room {room_id: $room_id})
            OPTIONAL MATCH (p:Patient)-[:LOCATED_IN]->(r)
            RETURN r.capacity as capacity, count(p) as current_occupancy
            """
            results = await run_query(query, {"room_id": room_id})
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
        try:
            rooms = ["ER01", "ICU01", "WARD_A01", "WARD_B01", "LAB01", "PHARM01"]
            room_states = {}
            for room in rooms:
                room_states[room] = await self.get_room_occupancy(room)

            query = """
            MATCH (p:Patient)
            RETURN p.status as status, count(p) as count
            """
            patient_status_counts = {}
            results = await run_query(query)
            for record in results:
                patient_status_counts[record["status"]] = record["count"]

            query = """
            MATCH (a:Agent)
            RETURN a.status as status, count(a) as count
            """
            agent_status_counts = {}
            results = await run_query(query)
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
