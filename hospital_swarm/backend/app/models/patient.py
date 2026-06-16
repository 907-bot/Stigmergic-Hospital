from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PatientBase(BaseModel):
    patient_id: str = Field(..., example="P001")
    severity: float = Field(..., ge=0.0, le=1.0, example=0.9)
    condition: str = Field(..., example="heart_attack")
    status: str = Field(..., example="waiting")
    heart_rate: Optional[int] = Field(None, example=88)
    bp_systolic: Optional[int] = Field(None, example=140)
    bp_diastolic: Optional[int] = Field(None, example=90)
    o2_saturation: Optional[int] = Field(None, example=97)
    temperature: Optional[float] = Field(None, example=37.2)

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    severity: Optional[float] = Field(None, ge=0.0, le=1.0)
    condition: Optional[str] = None
    status: Optional[str] = None
    heart_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    o2_saturation: Optional[int] = None
    temperature: Optional[float] = None

class Patient(PatientBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
