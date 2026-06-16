import asyncio
import uuid as uuid_mod
from typing import Dict, Any, Optional, List
from app.services.patient_service import PatientService
from app.services.pheromone_service import PheromoneService
from app.services.agent_service import AgentService
from app.services.hospital_service import HospitalService
from app.websockets.manager import manager
from app.models.agent import AgentCreate, Agent
from app.models.patient import PatientCreate, PatientUpdate
from app.models.pheromone import PheromoneCreate
import random
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

SCENARIO_VITALS = {
    "heart_attack": {"hr": (100, 140), "bp_sys": (140, 180), "bp_dia": (80, 100), "o2": (88, 95), "temp": (36.5, 37.5)},
    "stroke": {"hr": (80, 120), "bp_sys": (150, 200), "bp_dia": (90, 110), "o2": (92, 97), "temp": (36.5, 37.5)},
    "trauma": {"hr": (110, 150), "bp_sys": (90, 130), "bp_dia": (60, 80), "o2": (90, 96), "temp": (36.0, 37.0)},
    "fracture": {"hr": (70, 100), "bp_sys": (110, 140), "bp_dia": (70, 90), "o2": (95, 100), "temp": (36.5, 37.5)},
    "fever": {"hr": (90, 130), "bp_sys": (100, 130), "bp_dia": (65, 85), "o2": (94, 99), "temp": (38.5, 40.5)},
}

ACUITY_BY_SEVERITY = [
    (0.8, "IMMEDIATE"),
    (0.5, "URGENT"),
    (0.3, "STANDARD"),
    (0.0, "NON_URGENT"),
]

DETERIORATION_THRESHOLDS = {
    "hr": {"critical": 140, "warning": 120},
    "o2": {"critical": 88, "warning": 92},
    "temp": {"critical": 40.0, "warning": 39.0},
}

def get_acuity(severity: float) -> str:
    for threshold, level in ACUITY_BY_SEVERITY:
        if severity >= threshold:
            return level
    return "NON_URGENT"

def generate_vitals(scenario: str) -> dict:
    ranges = SCENARIO_VITALS.get(scenario, SCENARIO_VITALS["fever"])
    return {
        "heart_rate": random.randint(*ranges["hr"]),
        "bp_systolic": random.randint(*ranges["bp_sys"]),
        "bp_diastolic": random.randint(*ranges["bp_dia"]),
        "o2_saturation": random.randint(*ranges["o2"]),
        "temperature": round(random.uniform(*ranges["temp"]), 1),
    }

def check_deterioration(vitals: dict) -> Optional[str]:
    reasons = []
    if vitals.get("heart_rate", 0) > DETERIORATION_THRESHOLDS["hr"]["critical"]:
        reasons.append(f"HR {vitals['heart_rate']} (critical)")
    elif vitals.get("heart_rate", 0) > DETERIORATION_THRESHOLDS["hr"]["warning"]:
        reasons.append(f"HR {vitals['heart_rate']} (elevated)")
    if vitals.get("o2_saturation", 100) < DETERIORATION_THRESHOLDS["o2"]["critical"]:
        reasons.append(f"O2 {vitals['o2_saturation']}% (critical)")
    elif vitals.get("o2_saturation", 100) < DETERIORATION_THRESHOLDS["o2"]["warning"]:
        reasons.append(f"O2 {vitals['o2_saturation']}% (low)")
    if vitals.get("temperature", 36.0) > DETERIORATION_THRESHOLDS["temp"]["critical"]:
        reasons.append(f"Temp {vitals['temperature']}C (critical)")
    elif vitals.get("temperature", 36.0) > DETERIORATION_THRESHOLDS["temp"]["warning"]:
        reasons.append(f"Temp {vitals['temperature']}C (elevated)")
    if reasons:
        return "; ".join(reasons)
    return None

class SimulationService:
    def __init__(self):
        self.patient_service = PatientService()
        self.pheromone_service = PheromoneService()
        self.agent_service = AgentService()
        self.hospital_service = HospitalService()
        self._simulation_task: Optional[asyncio.Task] = None
        self._escalation_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._config = {
            "patient_arrival_rate": 5,
            "disease_scenarios": ["heart_attack", "fracture", "stroke", "trauma", "fever"],
            "severity_range": [0.1, 1.0],
            "enable_pheromone_engine": True,
            "evaporation_rate": 0.1,
            "diffusion_rate": 0.05,
            "deterioration_rate": 0.15,
            "escalation_time": 60,
        }
        self._stats = {
            "patients_generated": 0,
            "pheromones_created": 0,
            "deteriorations": 0,
            "escalations": 0,
            "agents_actions": 0,
            "start_time": None
        }
        self._broadcast_interval = 5
        self._last_broadcast = datetime.now()
        self._patient_vitals_cache: Dict[str, dict] = {}
        self._last_deterioration: Dict[str, datetime] = {}

    async def start_simulation(self) -> Dict[str, Any]:
        if self._is_running:
            return {"status": "already_running", "message": "Simulation is already running"}

        self._is_running = True
        self._stats["start_time"] = datetime.now().isoformat()

        try:
            await self.hospital_service.initialize_hospital()
        except Exception as e:
            logger.warning(f"Failed to initialize hospital: {e}")

        await self._initialize_default_agents()

        self._simulation_task = asyncio.create_task(self._simulation_loop())
        self._escalation_task = asyncio.create_task(self._escalation_loop())
        return {"status": "started", "message": "Simulation started"}

    async def stop_simulation(self) -> Dict[str, Any]:
        if not self._is_running:
            return {"status": "not_running", "message": "Simulation is not running"}

        self._is_running = False
        for task in [self._simulation_task, self._escalation_task]:
            if task:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._simulation_task = None
        self._escalation_task = None
        return {"status": "stopped", "message": "Simulation stopped"}

    async def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self._is_running,
            "stats": self._stats,
            "config": self._config,
            "resources": self.pheromone_service.get_resource_status(),
        }

    async def reset_simulation(self) -> Dict[str, Any]:
        was_running = self._is_running
        if was_running:
            await self.stop_simulation()

        self._stats = {
            "patients_generated": 0,
            "pheromones_created": 0,
            "deteriorations": 0,
            "escalations": 0,
            "agents_actions": 0,
            "start_time": None
        }
        self._patient_vitals_cache = {}

        if was_running:
            await self.start_simulation()

        return {"status": "reset", "message": "Simulation reset"}

    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        self._config.update(config)
        return {"status": "configured", "config": self._config}

    async def _initialize_default_agents(self):
        try:
            existing_agents = await self.agent_service.get_agents(limit=1)
            if existing_agents:
                return

            default_agents = [
                {"agent_id": "NURSE01", "role": "nurse", "status": "available"},
                {"agent_id": "NURSE02", "role": "nurse", "status": "available"},
                {"agent_id": "DOC01", "role": "doctor", "status": "available"},
                {"agent_id": "DOC02", "role": "doctor", "status": "available"},
                {"agent_id": "ICU01", "role": "icu", "status": "available"},
                {"agent_id": "LAB01", "role": "lab", "status": "available"},
                {"agent_id": "PHARM01", "role": "pharmacy", "status": "available"},
                {"agent_id": "AMB01", "role": "ambulance", "status": "available"},
            ]

            for agent_data in default_agents:
                agent_in = AgentCreate(**agent_data)
                await self.agent_service.create_agent(agent_in)
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")

    async def _simulation_loop(self):
        try:
            await asyncio.sleep(2)
            while self._is_running:
                await self._generate_patients()
                await self._update_vitals_and_deterioration()

                if self._config["enable_pheromone_engine"]:
                    await self.pheromone_service.evaporate_pheromones(
                        self._config["evaporation_rate"]
                    )
                    await self.pheromone_service.diffuse_pheromones(
                        self._config["diffusion_rate"]
                    )

                now = datetime.now()
                if (now - self._last_broadcast).total_seconds() >= self._broadcast_interval:
                    await self._broadcast_state()
                    self._last_broadcast = now

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Simulation loop error: {e}", exc_info=True)
            self._is_running = False

    async def _escalation_loop(self):
        try:
            while self._is_running:
                await asyncio.sleep(15)
                if not self._is_running:
                    break

                stale = await self.pheromone_service.get_stale_pheromones(
                    self._config["escalation_time"]
                )
                for p in stale:
                    if p.type == "TRIAGED":
                        esc_type = "ESCALATED"
                    else:
                        esc_type = "CRITICAL_ESCALATION"

                    # Check if already escalated
                    if p.escalated:
                        continue

                    await self.pheromone_service.expire_pheromone(p.pheromone_id)
                    await self.pheromone_service.create_pheromone(
                        PheromoneCreate(
                            pheromone_id=f"PHR{str(uuid_mod.uuid4().int)[:8]}",
                            type=esc_type,
                            strength=min(1.0, p.strength * 1.5),
                            ttl=120,
                            patient_id=p.patient_id,
                            status="active",
                            acuity=p.acuity or "",
                            escalated=True,
                            escalated_from=p.type,
                            sbar_situation=f"UNATTENDED {p.type} for patient {p.patient_id}",
                            sbar_assessment=f"Action required! {p.type} was not completed in time.",
                            sbar_recommendation="Immediate attention required",
                        )
                    )
                    self._stats["escalations"] += 1

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Escalation loop error: {e}", exc_info=True)

    async def _generate_patients(self):
        arrival_rate = self._config["patient_arrival_rate"] / 60.0
        if random.random() < arrival_rate:
            scenario = random.choice(self._config["disease_scenarios"])
            severity = random.uniform(*self._config["severity_range"])
            vitals = generate_vitals(scenario)

            patient_data = PatientCreate(
                patient_id=f"P{uuid_mod.uuid4().hex[:12]}",
                severity=severity,
                condition=scenario,
                status="waiting",
                **vitals,
            )

            await self.patient_service.create_patient(patient_data)
            self._stats["patients_generated"] += 1
            self._patient_vitals_cache[patient_data.patient_id] = vitals

            acuity = get_acuity(severity)
            if scenario in ["heart_attack", "stroke", "trauma", "fever", "fracture"] and severity > 0.2:
                pheromone_data = PheromoneCreate(
                    pheromone_id=f"PHR{int(datetime.now().timestamp())}{random.randint(100, 999)}",
                    type="EMERGENCY",
                    strength=severity,
                    ttl=300,
                    patient_id=patient_data.patient_id,
                    acuity=acuity,
                    vitals_hr=vitals["heart_rate"],
                    vitals_bp_systolic=vitals["bp_systolic"],
                    vitals_bp_diastolic=vitals["bp_diastolic"],
                    vitals_o2=vitals["o2_saturation"],
                    vitals_temp=vitals["temperature"],
                )
                await self.pheromone_service.create_pheromone(pheromone_data)
                self._stats["pheromones_created"] += 1

    async def _update_vitals_and_deterioration(self):
        if random.random() > self._config["deterioration_rate"]:
            return

        active_pheromones = await self.pheromone_service.get_pheromones(limit=50)
        patient_ids = set(p.patient_id for p in active_pheromones if p.patient_id)

        for pid in patient_ids:
            if pid not in self._patient_vitals_cache:
                continue

            vitals = self._patient_vitals_cache[pid]
            delta = random.choice([-1, 0, 0, 1])
            new_vitals = {
                "heart_rate": max(40, min(200, vitals["heart_rate"] + delta * random.randint(1, 5))),
                "bp_systolic": max(70, min(220, vitals["bp_systolic"] + delta * random.randint(1, 10))),
                "bp_diastolic": max(40, min(130, vitals["bp_diastolic"] + delta * random.randint(1, 5))),
                "o2_saturation": max(75, min(100, vitals["o2_saturation"] + delta * random.randint(0, 2))),
                "temperature": round(max(35.0, min(42.0, vitals["temperature"] + delta * random.uniform(0, 0.3))), 1),
            }
            self._patient_vitals_cache[pid] = new_vitals

            await self.patient_service.update_patient(
                pid,
                PatientUpdate(**new_vitals)
            )

            deterioration_reason = check_deterioration(new_vitals)
            if deterioration_reason:
                last_det = self._last_deterioration.get(pid)
                if last_det and (datetime.now() - last_det).total_seconds() < 30:
                    continue
                self._last_deterioration[pid] = datetime.now()
                await self.pheromone_service.create_pheromone(
                    PheromoneCreate(
                        pheromone_id=f"PHR{int(datetime.now().timestamp())}{random.randint(100, 999)}",
                        type="DETERIORATION",
                        strength=0.9,
                        ttl=120,
                        patient_id=pid,
                        status="active",
                        acuity="IMMEDIATE",
                        sbar_situation=f"Patient deteriorating: {deterioration_reason}",
                        vitals_hr=new_vitals["heart_rate"],
                        vitals_bp_systolic=new_vitals["bp_systolic"],
                        vitals_bp_diastolic=new_vitals["bp_diastolic"],
                        vitals_o2=new_vitals["o2_saturation"],
                        vitals_temp=new_vitals["temperature"],
                    )
                )
                self._stats["deteriorations"] += 1
                self._stats["pheromones_created"] += 1

    async def _broadcast_state(self):
        if manager.active_connections:
            broadcast_data = {
                "type": "simulation_update",
                "timestamp": datetime.now().isoformat(),
                "simulation": {
                    "is_running": self._is_running,
                    "stats": self._stats,
                    "config": self._config,
                    "resources": self.pheromone_service.get_resource_status(),
                }
            }
            await manager.broadcast(json.dumps(broadcast_data))
