import asyncio
from typing import Dict, Any, Optional, List
from app.services.patient_service import PatientService
from app.services.pheromone_service import PheromoneService
from app.services.agent_service import AgentService
from app.services.hospital_service import HospitalService
from app.websockets.manager import manager
from app.models.agent import AgentCreate, Agent
from app.models.patient import PatientUpdate
import random
from datetime import datetime, timedelta
import json

class SimulationService:
    def __init__(
        self,
        patient_service: PatientService = None,
        pheromone_service: PheromoneService = None,
        agent_service: AgentService = None,
        hospital_service: HospitalService = None
    ):
        self.patient_service = patient_service or PatientService()
        self.pheromone_service = pheromone_service or PheromoneService()
        self.agent_service = agent_service or AgentService()
        self.hospital_service = hospital_service or HospitalService()
        self._simulation_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._config = {
            "patient_arrival_rate": 5,  # patients per minute
            "disease_scenarios": ["heart_attack", "fracture", "stroke", "trauma", "fever"],
            "severity_range": [0.1, 1.0],
            "enable_pheromone_engine": True,
            "evaporation_rate": 0.1,
            "diffusion_rate": 0.05
        }
        self._stats = {
            "patients_generated": 0,
            "pheromones_created": 0,
            "agents_actions": 0,
            "start_time": None
        }
        self._broadcast_interval = 5  # seconds
        self._last_broadcast = datetime.now()

    async def start_simulation(self) -> Dict[str, Any]:
        if self._is_running:
            return {"status": "already_running", "message": "Simulation is already running"}

        self._is_running = True
        self._stats["start_time"] = datetime.now().isoformat()
        
        # Initialize hospital infrastructure
        try:
            await self.hospital_service.initialize_hospital()
            print("Hospital infrastructure initialized")
        except Exception as e:
            print(f"Warning: Failed to initialize hospital infrastructure: {e}")
            # Continue anyway, as the simulation can run without hospital infrastructure initially
        
        # Initialize default agents if none exist
        await self._initialize_default_agents()
        
        # Start the simulation loop in the background
        self._simulation_task = asyncio.create_task(self._simulation_loop())
        return {"status": "started", "message": "Simulation started"}

    async def stop_simulation(self) -> Dict[str, Any]:
        if not self._is_running:
            return {"status": "not_running", "message": "Simulation is not running"}

        self._is_running = False
        if self._simulation_task:
            self._simulation_task.cancel()
            try:
                await self._simulation_task
            except asyncio.CancelledError:
                pass
            self._simulation_task = None
        return {"status": "stopped", "message": "Simulation stopped"}

    async def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self._is_running,
            "stats": self._stats,
            "config": self._config
        }

    async def reset_simulation(self) -> Dict[str, Any]:
        was_running = self._is_running
        if was_running:
            await self.stop_simulation()
        
        # Reset statistics
        self._stats = {
            "patients_generated": 0,
            "pheromones_created": 0,
            "agents_actions": 0,
            "start_time": None
        }
        
        if was_running:
            await self.start_simulation()
        
        return {"status": "reset", "message": "Simulation reset"}

    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Update configuration
        self._config.update(config)
        return {"status": "configured", "config": self._config}

    async def _initialize_default_agents(self):
        """Create a default set of agents if none exist in the system"""
        try:
            # Check if there are any agents
            existing_agents = await self.agent_service.get_agents(limit=1)
            if existing_agents:
                # Agents already exist, skip initialization
                return

            # Define default agents to create
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

            # Create each agent
            for agent_data in default_agents:
                agent_in = AgentCreate(**agent_data)
                await self.agent_service.create_agent(agent_in)
                print(f"Created default agent: {agent_in.agent_id} ({agent_in.role})")

        except Exception as e:
            print(f"Error initializing default agents: {e}")

    async def _simulation_loop(self):
        """Main simulation loop"""
        try:
            while self._is_running:
                # Generate new patients based on arrival rate
                await self._generate_patients()
                
                # Update pheromones (evaporation and diffusion)
                if self._config["enable_pheromone_engine"]:
                    await self.pheromone_service.evaporate_pheromones(
                        self._config["evaporation_rate"]
                    )
                    await self.pheromone_service.diffuse_pheromones(
                        self._config["diffusion_rate"]
                    )
                
                # Let agents act based on current pheromones
                await self._simulate_agent_actions()
                
                # Check if it's time to broadcast
                now = datetime.now()
                if (now - self._last_broadcast).total_seconds() >= self._broadcast_interval:
                    await self._broadcast_state()
                    self._last_broadcast = now
                
                # Wait for next iteration (adjustable based on desired simulation speed)
                await asyncio.sleep(1)  # 1 second per simulation step
        except asyncio.CancelledError:
            # Clean up if cancelled
            pass
        except Exception as e:
            print(f"Simulation loop error: {e}")
            self._is_running = False

    async def _generate_patients(self):
        """Generate synthetic patients based on arrival rate"""
        # Simple Poisson process for patient arrivals
        # In a real implementation, we would use a more sophisticated model
        arrival_rate = self._config["patient_arrival_rate"] / 60.0  # per second
        if random.random() < arrival_rate:
            # Generate a patient
            scenario = random.choice(self._config["disease_scenarios"])
            severity = random.uniform(*self._config["severity_range"])
            
            patient_data = {
                "patient_id": f"P{int(datetime.now().timestamp())}{random.randint(100, 999)}",
                "severity": severity,
                "condition": scenario,
                "status": "waiting"
            }
            
            await self.patient_service.create_patient(patient_data)
            self._stats["patients_generated"] += 1
            
            # If emergency condition, create an emergency pheromone
            if scenario in ["heart_attack", "stroke", "trauma"] and severity > 0.7:
                pheromone_data = {
                    "type": "EMERGENCY",
                    "strength": severity,
                    "ttl": 300  # 5 minutes
                }
                await self.pheromone_service.create_pheromone(pheromone_data)
                self._stats["pheromones_created"] += 1

    async def _simulate_agent_actions(self):
        """Simulate agents taking actions based on pheromones"""
        try:
            # Get current agents and pheromones
            agents = await self.agent_service.get_agents(limit=100)  # Get a reasonable number of agents
            pheromones = await self.pheromone_service.get_pheromones(limit=100)  # Get active pheromones
            
            # Decide actions for agents based on pheromones
            actions = await self.agent_service.decide_actions(agents, pheromones)
            
            # Execute the actions (update patient states, assign resources, etc.)
            executed_actions = await self._execute_agent_actions(agents, actions)
            
            # Update the stats with the number of actions executed
            self._stats["agents_actions"] += len(executed_actions)
            
            # Optionally, log the actions for debugging
            if executed_actions:
                print(f"Agents executed actions: {executed_actions}")
        except Exception as e:
            print(f"Error in agent action simulation: {e}")

    async def _execute_agent_actions(self, agents: List[Agent], actions: List[str]) -> List[str]:
        """Execute agent actions by updating the hospital state"""
        executed = []
        
        # Create a mapping of agent_id to agent for easy lookup
        agent_map = {agent.agent_id: agent for agent in agents}
        
        for action_str in actions:
            try:
                # Parse the action string to extract agent ID and action type
                # Format examples:
                # "Nurse NURSE01 triaged patient (emergency strength: 0.85)"
                # "Doctor DOC01 diagnosed patient (emergency strength: 0.92)"
                # "ICU ICU01 prepared bed (emergency strength: 0.88)"
                # etc.
                
                if not action_str or ' ' not in action_str:
                    continue
                    
                # Extract agent ID (assumes format like "NURSE01", "DOC01", etc.)
                parts = action_str.split(' ')
                if len(parts) < 2:
                    continue
                    
                agent_id = parts[1]  # Second part should be the agent ID
                
                # Find the agent
                agent = agent_map.get(agent_id)
                if not agent:
                    continue
                
                # Execute different actions based on agent role and action type
                if "triaged patient" in action_str:
                    # Nurse triaged a patient - assign a waiting patient to this nurse
                    await self._assign_waiting_patient_to_nurse(agent_id)
                    executed.append(action_str)
                    
                elif "diagnosed patient" in action_str:
                    # Doctor diagnosed a patient - move patient from waiting to being treated
                    # For now, we'll just mark it as an action
                    executed.append(action_str)
                    
                elif "prepared bed" in action_str:
                    # ICU prepared a bed - we'll note this in logs
                    executed.append(action_str)
                    
                elif "scheduled tests" in action_str:
                    # Lab scheduled tests
                    executed.append(action_str)
                    
                elif "prepared medications" in action_str:
                    # Pharmacy prepared medications
                    executed.append(action_str)
                    
                elif "dispatched" in action_str:
                    # Ambulance dispatched
                    executed.append(action_str)
                    
            except Exception as e:
                print(f"Error executing action '{action_str}': {e}")
                continue
                
        return executed

    async def _assign_waiting_patient_to_nurse(self, nurse_id: str):
        """Assign a waiting patient to a nurse"""
        try:
            # Get a waiting patient
            waiting_patients = await self.patient_service.get_waiting_patients(limit=1)
            if not waiting_patients:
                return
                
            patient = waiting_patients[0]
            
            # Assign patient to nurse
            await self.hospital_service.assign_patient_to_agent(
                patient.patient_id, 
                nurse_id, 
                "ASSIGNED_TO"
            )
            
            # Update patient status to "being_treated"
            await self.patient_service.update_patient(
                patient.patient_id, 
                PatientUpdate(status="being_treated")
            )
            
            # Optionally, assign to a room (e.g., ER for emergency cases)
            # For simplicity, we'll just note the assignment
            
        except Exception as e:
            print(f"Error assigning patient to nurse {nurse_id}: {e}")

    async def _broadcast_state(self):
        """Broadcast the current simulation state to all connected WebSocket clients"""
        if manager.active_connections:
            broadcast_data = {
                "type": "simulation_update",
                "timestamp": datetime.now().isoformat(),
                "simulation": {
                    "is_running": self._is_running,
                    "stats": self._stats,
                    "config": self._config
                }
            }
            await manager.broadcast(json.dumps(broadcast_data))