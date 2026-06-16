from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.pheromone_service import PheromoneService
from app.services.patient_service import PatientService
from app.models.pheromone import ACUITY_TIERS

router = APIRouter()


@router.get("/{patient_id}", response_model=Dict[str, Any])
async def get_patient_journey(patient_id: str):
    p_service = PatientService()
    ph_service = PheromoneService()

    patient = await p_service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    pheromones = await ph_service.get_pheromones_for_patient(patient_id)

    timeline = []
    for p in pheromones:
        entry = {
            "pheromone_id": p.pheromone_id,
            "type": p.type,
            "status": p.status,
            "strength": p.strength,
            "created_at": p.created_at.isoformat() if hasattr(p, 'created_at') else None,
            "expires_at": p.expires_at.isoformat() if hasattr(p, 'expires_at') else None,
            "acuity": p.acuity or "",
        }
        if p.medication_name:
            entry["medication_name"] = p.medication_name
        if p.medication_dosage:
            entry["medication_dosage"] = p.medication_dosage
        if p.test_type:
            entry["test_type"] = p.test_type
        if p.test_result:
            entry["test_result"] = p.test_result
        if p.sbar_situation:
            entry["sbar_situation"] = p.sbar_situation
        if p.sbar_assessment:
            entry["sbar_assessment"] = p.sbar_assessment
        if p.escalated:
            entry["escalated"] = True
        if p.escalated_from:
            entry["escalated_from"] = p.escalated_from
        timeline.append(entry)

    return {
        "patient_id": patient.patient_id,
        "condition": patient.condition,
        "severity": patient.severity,
        "status": patient.status,
        "vitals": {
            "heart_rate": patient.heart_rate,
            "bp_systolic": patient.bp_systolic,
            "bp_diastolic": patient.bp_diastolic,
            "o2_saturation": patient.o2_saturation,
            "temperature": patient.temperature,
        },
        "timeline": timeline,
    }
