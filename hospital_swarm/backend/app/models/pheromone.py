from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

ACUITY_TIERS = {
    "IMMEDIATE": {"ttl": 60, "label": "Immediate", "color": "#d32f2f"},
    "URGENT": {"ttl": 180, "label": "Urgent", "color": "#f57c00"},
    "STANDARD": {"ttl": 300, "label": "Standard", "color": "#1976d2"},
    "NON_URGENT": {"ttl": 600, "label": "Non-Urgent", "color": "#388e3c"},
}

class PheromoneBase(BaseModel):
    pheromone_id: str = Field(..., example="PHR001")
    type: str = Field(..., example="EMERGENCY")
    strength: float = Field(..., ge=0.0, le=1.0, example=0.95)
    ttl: int = Field(..., example=300)
    expires_at: Optional[datetime] = Field(None, example="2024-06-02T12:00:00Z")
    patient_id: Optional[str] = Field(None, example="P123")
    status: str = Field("active", example="active")
    medication_name: Optional[str] = Field(None, example="Aspirin")
    medication_dosage: Optional[str] = Field(None, example="100mg daily")
    test_type: Optional[str] = Field(None, example="Blood Culture")
    test_result: Optional[str] = Field(None, example="Positive for Streptococcus")
    acuity: Optional[str] = Field(None, example="URGENT")
    escalated: bool = Field(False, example=False)
    escalated_from: Optional[str] = Field(None, example="TRIAGED")
    sbar_situation: Optional[str] = Field(None, example="75yo male with chest pain")
    sbar_background: Optional[str] = Field(None, example="History of hypertension")
    sbar_assessment: Optional[str] = Field(None, example="Possible MI")
    sbar_recommendation: Optional[str] = Field(None, example="Immediate cardiology consult")
    vitals_hr: Optional[int] = Field(None, example=88)
    vitals_bp_systolic: Optional[int] = Field(None, example=140)
    vitals_bp_diastolic: Optional[int] = Field(None, example=90)
    vitals_o2: Optional[int] = Field(None, example=97)
    vitals_temp: Optional[float] = Field(None, example=37.2)

class PheromoneCreate(PheromoneBase):
    pass

class PheromoneUpdate(BaseModel):
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    ttl: Optional[int] = None
    status: Optional[str] = None
    test_result: Optional[str] = None

class Pheromone(PheromoneBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
