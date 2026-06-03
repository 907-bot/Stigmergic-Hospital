from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PatientBase(BaseModel):
    patient_id: str = Field(..., example="P001")
    severity: float = Field(..., ge=0.0, le=1.0, example=0.9)
    condition: str = Field(..., example="heart_attack")
    status: str = Field(..., example="waiting")

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    severity: Optional[float] = Field(None, ge=0.0, le=1.0)
    condition: Optional[str] = None
    status: Optional[str] = None

class Patient(PatientBase):
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True