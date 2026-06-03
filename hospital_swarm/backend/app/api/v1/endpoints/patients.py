from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models.patient import Patient, PatientCreate, PatientUpdate
from app.services.patient_service import PatientService

router = APIRouter()

@router.get("/", response_model=List[Patient])
async def list_patients(skip: int = 0, limit: int = 100, patient_service: PatientService = Depends()):
    return await patient_service.get_patients(skip=skip, limit=limit)

@router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient(patient_in: PatientCreate, patient_service: PatientService = Depends()):
    return await patient_service.create_patient(patient_in)

@router.get("/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str, patient_service: PatientService = Depends()):
    patient = await patient_service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/{patient_id}", response_model=Patient)
async def update_patient(
    patient_id: str, 
    patient_in: PatientUpdate, 
    patient_service: PatientService = Depends()
):
    patient = await patient_service.update_patient(patient_id, patient_in)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: str, patient_service: PatientService = Depends()):
    success = await patient_service.delete_patient(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return None