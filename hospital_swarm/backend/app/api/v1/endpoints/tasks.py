import uuid
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from app.services.pheromone_service import (
    PheromoneService, ROLE_TASKS, ROLE_ACTIONS, ACUITY_TIERS
)
from app.models.pheromone import Pheromone, PheromoneCreate
from pydantic import BaseModel

router = APIRouter()


class MedicationItem(BaseModel):
    name: str = ""
    dosage: str = ""


class SBARNotes(BaseModel):
    situation: str = ""
    background: str = ""
    assessment: str = ""
    recommendation: str = ""


class TriageRequest(BaseModel):
    sbar: Optional[SBARNotes] = None


class DiagnoseRequest(BaseModel):
    order_lab_tests: bool = False
    lab_test_type: str = "Blood Test"
    request_icu: bool = False
    prescribe_medication: bool = False
    medications: List[MedicationItem] = []


class LabCompleteRequest(BaseModel):
    test_type: str = ""
    test_result: str = ""


@router.get("/", response_model=List[Dict[str, Any]])
async def get_tasks(role: str = "nurse"):
    role = role.lower()
    if role not in ROLE_TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown role: {role}. Valid roles: {', '.join(ROLE_TASKS.keys())}")

    service = PheromoneService()
    pheromone_types = ROLE_TASKS[role]
    pheromones = await service.get_pheromones_by_type(pheromone_types)

    tasks = []
    for p in pheromones:
        action_name, _ = ROLE_ACTIONS[role]
        task = {
            "id": p.pheromone_id,
            "type": p.type,
            "strength": p.strength,
            "patient_id": p.patient_id or "",
            "action": action_name,
            "role": role,
            "created_at": p.created_at.isoformat() if hasattr(p, 'created_at') else None,
            "acuity": p.acuity or "",
            "escalated": p.escalated,
            "escalated_from": p.escalated_from or "",
        }
        if p.medication_name:
            task["medication_name"] = p.medication_name
        if p.medication_dosage:
            task["medication_dosage"] = p.medication_dosage
        if p.test_type:
            task["test_type"] = p.test_type
        if p.test_result:
            task["test_result"] = p.test_result
        if p.sbar_situation:
            task["sbar_situation"] = p.sbar_situation
        if p.sbar_background:
            task["sbar_background"] = p.sbar_background
        if p.sbar_assessment:
            task["sbar_assessment"] = p.sbar_assessment
        if p.sbar_recommendation:
            task["sbar_recommendation"] = p.sbar_recommendation
        if p.vitals_hr:
            task["vitals_hr"] = p.vitals_hr
        if p.vitals_bp_systolic:
            task["vitals_bp_systolic"] = p.vitals_bp_systolic
        if p.vitals_bp_diastolic:
            task["vitals_bp_diastolic"] = p.vitals_bp_diastolic
        if p.vitals_o2:
            task["vitals_o2"] = p.vitals_o2
        if p.vitals_temp:
            task["vitals_temp"] = p.vitals_temp
        tasks.append(task)

    acuity_order = {"IMMEDIATE": 0, "URGENT": 1, "STANDARD": 2, "NON_URGENT": 3, "": 4}
    tasks.sort(key=lambda t: (acuity_order.get(t.get("acuity", ""), 4), -t.get("strength", 0)))
    return tasks


@router.post("/{task_id}/perform", response_model=Dict[str, Any])
async def perform_task(task_id: str, role: str = "nurse"):
    role = role.lower()
    if role not in ROLE_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Unknown role: {role}")

    action_name, next_type = ROLE_ACTIONS[role]
    service = PheromoneService()

    existing = await service.get_pheromone_by_id(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or expired")

    next_pheromone = await service.complete_and_create_next(task_id, role, next_type)

    result = {
        "status": "completed",
        "action": action_name,
        "role": role,
        "completed_task": task_id,
        "patient_id": existing.patient_id,
    }
    if next_pheromone:
        result["next_type"] = next_type
        result["next_pheromone_id"] = next_pheromone.pheromone_id

    return result


@router.post("/{task_id}/triage", response_model=Dict[str, Any])
async def triage_patient(task_id: str, req: TriageRequest):
    service = PheromoneService()

    existing = await service.get_pheromone_by_id(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or expired")

    acuity_level = existing.acuity or "STANDARD"

    kwargs = {}
    if req.sbar:
        kwargs["sbar_situation"] = req.sbar.situation
        kwargs["sbar_background"] = req.sbar.background
        kwargs["sbar_assessment"] = req.sbar.assessment
        kwargs["sbar_recommendation"] = req.sbar.recommendation

    kwargs["acuity"] = acuity_level
    kwargs["vitals_hr"] = existing.vitals_hr
    kwargs["vitals_bp_systolic"] = existing.vitals_bp_systolic
    kwargs["vitals_bp_diastolic"] = existing.vitals_bp_diastolic
    kwargs["vitals_o2"] = existing.vitals_o2
    kwargs["vitals_temp"] = existing.vitals_temp

    next_pheromone = await service.complete_and_create_next(task_id, "nurse", "TRIAGED", **kwargs)

    return {
        "status": "completed",
        "action": "triage",
        "completed_task": task_id,
        "patient_id": existing.patient_id,
        "acuity": acuity_level,
        "next_pheromone_id": next_pheromone.pheromone_id if next_pheromone else None,
    }


@router.post("/{task_id}/diagnose", response_model=Dict[str, Any])
async def diagnose_patient(task_id: str, req: DiagnoseRequest):
    service = PheromoneService()

    existing = await service.get_pheromone_by_id(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or expired")
    if existing.type not in ["TRIAGED", "ESCALATED", "CRITICAL_ESCALATION"]:
        raise HTTPException(status_code=400, detail="Only TRIAGED or escalated cases can be diagnosed")

    next_pheromones = []

    next_pheromones.append(PheromoneCreate(
        pheromone_id=f"PHR{str(uuid.uuid4().int)[:8]}",
        type="DIAGNOSED",
        strength=existing.strength * 0.9,
        ttl=300,
        patient_id=existing.patient_id,
        status="active",
        sbar_situation=existing.sbar_situation,
        sbar_background=existing.sbar_background,
        sbar_assessment=existing.sbar_assessment,
        sbar_recommendation=existing.sbar_recommendation,
        vitals_hr=existing.vitals_hr,
        vitals_bp_systolic=existing.vitals_bp_systolic,
        vitals_bp_diastolic=existing.vitals_bp_diastolic,
        vitals_o2=existing.vitals_o2,
        vitals_temp=existing.vitals_temp,
    ))

    if req.order_lab_tests:
        next_pheromones.append(PheromoneCreate(
            pheromone_id=f"PHR{str(uuid.uuid4().int)[:8]}",
            type="LAB_REQUEST",
            strength=existing.strength * 0.85,
            ttl=300,
            patient_id=existing.patient_id,
            status="active",
            test_type=req.lab_test_type,
            sbar_situation=existing.sbar_situation,
        ))

    if req.request_icu:
        available = service.use_resource("icu_beds")
        next_pheromones.append(PheromoneCreate(
            pheromone_id=f"PHR{str(uuid.uuid4().int)[:8]}",
            type="ICU_REQUEST",
            strength=existing.strength * 0.85,
            ttl=300,
            patient_id=existing.patient_id,
            status="active",
            sbar_situation=f"ICU bed requested for {existing.patient_id}" + ("" if available else " (NO BEDS AVAILABLE)"),
        ))
        if not available:
            shortages = await service.check_resource_shortages()
            for s in shortages:
                next_pheromones.append(PheromoneCreate(
                    pheromone_id=f"PHR{str(uuid.uuid4().int)[:8]}",
                    type="RESOURCE_SHORTAGE",
                    strength=0.95,
                    ttl=120,
                    patient_id="SYSTEM",
                    status="active",
                    sbar_situation=f"Resource shortage: {s}",
                ))

    if req.prescribe_medication and req.medications:
        for med in req.medications:
            if med.name:
                available = service.use_resource("pharmacy_stock")
                next_pheromones.append(PheromoneCreate(
                    pheromone_id=f"PHR{str(uuid.uuid4().int)[:8]}",
                    type="PRESCRIPTION",
                    strength=existing.strength * 0.85,
                    ttl=300,
                    patient_id=existing.patient_id,
                    status="active",
                    medication_name=med.name,
                    medication_dosage=med.dosage,
                    sbar_situation="" if available else f"OUT OF STOCK: {med.name}",
                ))

    created = await service.complete_and_create_multiple(task_id, next_pheromones)

    return {
        "status": "completed",
        "action": "diagnose",
        "completed_task": task_id,
        "patient_id": existing.patient_id,
        "created_pheromones": [p.type for p in created],
    }


@router.post("/{task_id}/lab-complete", response_model=Dict[str, Any])
async def lab_complete(task_id: str, req: LabCompleteRequest):
    service = PheromoneService()

    existing = await service.get_pheromone_by_id(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or expired")
    if existing.type != "LAB_REQUEST":
        raise HTTPException(status_code=400, detail="Only LAB_REQUEST pheromones can be completed with results")

    # Update the LAB_REQUEST with test result so it's preserved
    from app.models.pheromone import PheromoneUpdate
    await service.update_pheromone(task_id, PheromoneUpdate(test_result=req.test_result))

    # Create LAB_COMPLETE pheromone back to doctor
    next_pheromone = await service.complete_and_create_next(
        task_id, "lab", "LAB_COMPLETE",
        test_type=req.test_type or existing.test_type or "",
        test_result=req.test_result,
        sbar_situation=f"Lab results for {existing.patient_id}: {req.test_type or existing.test_type} = {req.test_result}",
    )

    return {
        "status": "completed",
        "action": "run_tests",
        "completed_task": task_id,
        "patient_id": existing.patient_id,
        "test_type": req.test_type or existing.test_type,
        "test_result": req.test_result,
        "next_pheromone_id": next_pheromone.pheromone_id if next_pheromone else None,
    }
