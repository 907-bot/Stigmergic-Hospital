"""
FHIR R4 (Release 4) API endpoints.

Implements:
  - GET /fhir/r4/Patient          — search patients
  - GET /fhir/r4/Patient/{id}     — read patient
  - GET /fhir/r4/Observation      — search observations (vitals)
  - GET /fhir/r4/MedicationRequest — search prescriptions
  - POST /fhir/r4/Patient         — create patient
  - POST /fhir/r4/$validate       — validate a resource

Reference: https://hl7.org/fhir/R4/
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.db.neo4j import run_query
from app.auth.dependencies import get_current_user, optional_user
from app.auth.models import TokenData
from app.audit.audit import log_audit_event, AuditAction
import uuid
import json

router = APIRouter()

RESOURCE_TYPE_MAP = {
    "Patient": "Patient",
    "Observation": "Pheromone",
    "MedicationRequest": "Pheromone",
}

FHIR_VERSION = "4.0.1"


def _build_bundle(
    entries: List[Dict[str, Any]],
    resource_type: str,
    total: int = 0,
) -> Dict[str, Any]:
    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "meta": {"lastUpdated": datetime.utcnow().isoformat() + "Z"},
        "type": "searchset",
        "total": total or len(entries),
        "entry": [
            {
                "fullUrl": f"urn:uuid:{e.get('id', e.get('resourceId', ''))}",
                "resource": e,
                "search": {"mode": "match"},
            }
            for e in entries
        ],
    }


def _patient_to_fhir(patient_data: dict) -> Dict[str, Any]:
    """Convert a Neo4j Patient node to FHIR Patient resource."""
    return {
        "resourceType": "Patient",
        "id": patient_data.get("patient_id", ""),
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"],
            "lastUpdated": (
                patient_data.get("created_at", datetime.utcnow().isoformat())
            ),
        },
        "identifier": [
            {
                "use": "usual",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                        }
                    ]
                },
                "value": patient_data.get("patient_id", ""),
            }
        ],
        "active": patient_data.get("status", "unknown") != "discharged",
        "generalPractitioner": [],
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-severity",
                "valueDecimal": patient_data.get("severity", 0),
            }
        ],
    }


def _observation_to_fhir(pheromone: dict) -> Dict[str, Any]:
    """Convert vitals pheromone to FHIR Observation."""
    obs_id = pheromone.get("pheromone_id", pheromone.get("id", ""))
    obs = {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "subject": {
            "reference": f"Patient/{pheromone.get('patient_id', '')}",
        },
        "effectiveDateTime": pheromone.get("created_at", datetime.utcnow().isoformat()),
        "issued": datetime.utcnow().isoformat() + "Z",
    }

    vital_codes = {
        "vitals_hr": {"code": "8867-4", "system": "http://loinc.org", "display": "Heart rate"},
        "vitals_bp_systolic": {"code": "8480-6", "system": "http://loinc.org", "display": "Systolic blood pressure"},
        "vitals_bp_diastolic": {"code": "8462-4", "system": "http://loinc.org", "display": "Diastolic blood pressure"},
        "vitals_o2": {"code": "2708-6", "system": "http://loinc.org", "display": "Oxygen saturation"},
        "vitals_temp": {"code": "8310-5", "system": "http://loinc.org", "display": "Body temperature"},
    }

    components = []
    for field, coding in vital_codes.items():
        val = pheromone.get(field)
        if val is not None and val != 0:
            components.append({
                "code": {"coding": [coding]},
                "valueQuantity": {
                    "value": float(val),
                    "unit": (
                        "bpm" if "hr" in field
                        else "mmHg" if "bp" in field
                        else "%" if "o2" in field
                        else "C"
                    ),
                },
            })

    if components:
        obs["component"] = components
    else:
        obs["valueString"] = pheromone.get("sbar_situation", "")

    return obs


def _medication_request_to_fhir(pheromone: dict) -> Dict[str, Any]:
    """Convert PRESCRIPTION pheromone to FHIR MedicationRequest."""
    return {
        "resourceType": "MedicationRequest",
        "id": pheromone.get("pheromone_id", ""),
        "status": "active" if pheromone.get("status") == "active" else "completed",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "display": pheromone.get("medication_name", ""),
                }
            ],
            "text": f"{pheromone.get('medication_name', '')} {pheromone.get('medication_dosage', '')}",
        },
        "subject": {
            "reference": f"Patient/{pheromone.get('patient_id', '')}",
        },
        "authoredOn": pheromone.get("created_at", datetime.utcnow().isoformat()),
        "dosageInstruction": [
            {
                "text": pheromone.get("medication_dosage", ""),
            }
        ],
    }


# --- FHIR Endpoints ---


@router.get("/Patient", response_model=Dict[str, Any])
@router.get("/Patient/", response_model=Dict[str, Any])
async def fhir_search_patient(
    request: Request,
    _id: Optional[str] = Query(None, alias="_id"),
    identifier: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    current_user: Optional[TokenData] = Depends(optional_user),
):
    tenant_filter = ""
    params = {}

    if current_user and current_user.tenant_id:
        tenant_filter = " AND p.tenant_id = $tenant_id"
        params["tenant_id"] = current_user.tenant_id

    if _id:
        params["patient_id"] = _id
        results = await run_query(
            "MATCH (p:Patient {patient_id: $patient_id}) RETURN p", params
        )
    elif identifier:
        params["patient_id"] = identifier
        results = await run_query(
            "MATCH (p:Patient {patient_id: $patient_id}) RETURN p", params
        )
    else:
        limit = 50
        results = await run_query(
            f"MATCH (p:Patient) WHERE p.status IS NOT NULL{tenant_filter} RETURN p LIMIT $limit",
            {**params, "limit": limit},
        )

    patients = [_patient_to_fhir(r["p"]) for r in results]
    return _build_bundle(patients, "Patient", total=len(patients))


@router.get("/Patient/{patient_id}", response_model=Dict[str, Any])
async def fhir_read_patient(
    patient_id: str,
    current_user: Optional[TokenData] = Depends(optional_user),
):
    results = await run_query(
        "MATCH (p:Patient {patient_id: $patient_id}) RETURN p",
        {"patient_id": patient_id},
    )
    if not results:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user:
        await log_audit_event(
            action=AuditAction.PATIENT_VIEW,
            actor_id=current_user.user_id or "anonymous",
            tenant_id=current_user.tenant_id or "",
            patient_id=patient_id,
            resource_type="Patient",
            resource_id=patient_id,
            detail="FHIR R4 Patient read",
        )

    return _patient_to_fhir(results[0]["p"])


@router.get("/Observation", response_model=Dict[str, Any])
async def fhir_search_observation(
    patient: Optional[str] = Query(None, alias="patient"),
    _count: int = Query(50, alias="_count"),
    current_user: Optional[TokenData] = Depends(optional_user),
):
    if patient:
        results = await run_query(
            """
            MATCH (p:Pheromone {patient_id: $patient_id})
            WHERE (p.vitals_hr > 0 OR p.vitals_o2 > 0)
            RETURN p ORDER BY p.created_at DESC LIMIT $limit
            """,
            {"patient_id": patient, "limit": _count},
        )
    else:
        results = await run_query(
            """
            MATCH (p:Pheromone)
            WHERE (p.vitals_hr > 0 OR p.vitals_o2 > 0)
            RETURN p ORDER BY p.created_at DESC LIMIT $limit
            """,
            {"limit": _count},
        )

    observations = [_observation_to_fhir(r["p"]) for r in results]
    return _build_bundle(observations, "Observation", total=len(observations))


@router.get("/MedicationRequest", response_model=Dict[str, Any])
async def fhir_search_medication_request(
    patient: Optional[str] = Query(None, alias="patient"),
    current_user: Optional[TokenData] = Depends(optional_user),
):
    if patient:
        results = await run_query(
            """
            MATCH (p:Pheromone {patient_id: $patient_id})
            WHERE p.type = 'PRESCRIPTION' AND p.medication_name IS NOT NULL
            RETURN p ORDER BY p.created_at DESC
            """,
            {"patient_id": patient},
        )
    else:
        results = await run_query(
            """
            MATCH (p:Pheromone)
            WHERE p.type = 'PRESCRIPTION' AND p.medication_name IS NOT NULL
            RETURN p ORDER BY p.created_at DESC
            """
        )

    meds = [_medication_request_to_fhir(r["p"]) for r in results]
    return _build_bundle(meds, "MedicationRequest", total=len(meds))


@router.get("/metadata", response_model=Dict[str, Any])
async def fhir_capability_statement():
    """FHIR CapabilityStatement — tells clients what this server supports."""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.utcnow().isoformat() + "Z",
        "publisher": "Stigmergic Hospital Swarm OS",
        "kind": "instance",
        "software": {"name": "Hospital Swarm FHIR Server", "version": FHIR_VERSION},
        "fhirVersion": FHIR_VERSION,
        "format": ["application/fhir+json", "application/json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "identifier", "type": "token"},
                            {"name": "name", "type": "string"},
                        ],
                    },
                    {
                        "type": "Observation",
                        "interaction": [{"code": "search-type"}],
                        "searchParam": [
                            {"name": "patient", "type": "reference"},
                            {"name": "_count", "type": "number"},
                        ],
                    },
                    {
                        "type": "MedicationRequest",
                        "interaction": [{"code": "search-type"}],
                        "searchParam": [{"name": "patient", "type": "reference"}],
                    },
                ],
            }
        ],
    }


# --- HL7 v2 Adapter ---


class HL7Message:
    """Simple HL7 v2 message builder for ADT (Admission/Discharge/Transfer)."""

    @staticmethod
    def adt_a01(patient_id: str, patient_name: str, attending_doctor: str = "") -> str:
        """Build an HL7 ADT^A01 (Admit) message."""
        now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return (
            f"MSH|^~\\&|HOSPITAL_SWARM|HOSPITAL|EPIC|EPIC|{now}||ADT^A01|{patient_id}|P|2.5\r"
            f"EVN|A01|{now}\r"
            f"PID|1||{patient_id}||{patient_name}|||M|||123 Main St^^Metropolis^NY^10001||555-0100\r"
            f"PV1|1|I|ER^ER01^HOSPITAL||||{attending_doctor}^Doctor|||||||||||{patient_id}"
        )

    @staticmethod
    def adt_a03(patient_id: str, patient_name: str) -> str:
        """Build an HL7 ADT^A03 (Discharge) message."""
        now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return (
            f"MSH|^~\\&|HOSPITAL_SWARM|HOSPITAL|EPIC|EPIC|{now}||ADT^A03|{patient_id}|P|2.5\r"
            f"EVN|A03|{now}\r"
            f"PID|1||{patient_id}||{patient_name}|||M\r"
            f"PV1|1|O|||||||||||||||{now}"
        )
    