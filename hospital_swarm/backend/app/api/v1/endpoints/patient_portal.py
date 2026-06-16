from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
import html
from app.services.patient_service import PatientService
from app.services.pheromone_service import PheromoneService, ROLE_ACTIONS, ROLE_TASKS, NEXT_STEP
from app.models.pheromone import ACUITY_TIERS

router = APIRouter()

def h(text: Any) -> str:
    return html.escape(str(text))

ROLE_NAMES = {
    "nurse": "Nurse",
    "doctor": "Doctor",
    "icu": "ICU Unit",
    "lab": "Lab",
    "pharmacy": "Pharmacy",
    "ambulance": "Ambulance",
}

ROLE_ICONS = {
    "nurse": "🩺",
    "doctor": "👨‍⚕️",
    "icu": "🏥",
    "lab": "🔬",
    "pharmacy": "💊",
    "ambulance": "🚑",
}

DETERIORATION_INDICATORS = {
    "Heart Rate": ("vitals_hr", {140: "Critical", 120: "Elevated"}),
    "O2 Saturation": ("vitals_o2", {92: "Low", 88: "Critical"}),
    "Temperature": ("vitals_temp", {39.0: "Elevated", 40.0: "Critical"}),
}


def get_role_for_pheromone_type(p_type: str) -> Optional[str]:
    for role, types in ROLE_TASKS.items():
        if p_type in types:
            return role
    return None


def get_current_step(active_pheromones: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not active_pheromones:
        return None
    # Return the most relevant active pheromone (highest strength first)
    ordered = sorted(active_pheromones, key=lambda p: -p.get("strength", 0))
    return ordered[0]


def get_next_step(p_type: str) -> Optional[Dict[str, Any]]:
    step = NEXT_STEP.get(p_type)
    if step:
        next_type, role = step
        return {
            "next_type": next_type,
            "role": role,
            "role_label": ROLE_NAMES.get(role, role),
            "role_icon": ROLE_ICONS.get(role, "❓"),
            "action": ROLE_ACTIONS.get(role, ("", ""))[0].replace("_", " "),
        }
    # Check if this type has a role assigned (for types that end the chain)
    role = get_role_for_pheromone_type(p_type)
    if role:
        return {
            "next_type": "completed",
            "role": role,
            "role_label": "All departments",
            "role_icon": "✅",
            "action": "Complete",
        }
    return None


@router.get("/{patient_id}", response_model=Dict[str, Any])
async def get_patient_portal(patient_id: str):
    p_service = PatientService()
    ph_service = PheromoneService()

    patient = await p_service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    all_pheromones = await ph_service.get_pheromones_for_patient(patient_id)
    active = [p for p in all_pheromones if p.status == "active"]
    completed = [p for p in all_pheromones if p.status == "completed"]

    active_tasks = []
    for p in active:
        entry = {
            "pheromone_id": p.pheromone_id,
            "type": p.type,
            "strength": p.strength,
            "created_at": p.created_at.isoformat() if hasattr(p, 'created_at') else None,
            "acuity": p.acuity or "",
        }
        role = get_role_for_pheromone_type(p.type)
        entry["handled_by"] = ROLE_NAMES.get(role, "System") if role else "System"
        if p.medication_name:
            entry["medication_name"] = p.medication_name
            entry["medication_dosage"] = p.medication_dosage
        if p.test_type:
            entry["test_type"] = p.test_type
        if p.test_result:
            entry["test_result"] = p.test_result
        if p.sbar_situation:
            entry["sbar_situation"] = p.sbar_situation
        if p.sbar_assessment:
            entry["sbar_assessment"] = p.sbar_assessment
        if p.sbar_recommendation:
            entry["sbar_recommendation"] = p.sbar_recommendation
        if p.escalated:
            entry["escalated"] = True
        active_tasks.append(entry)

    current = get_current_step(active_tasks)
    next_step = get_next_step(current["type"]) if current else None

    timeline_entries = []
    for p in sorted(all_pheromones, key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.min):
        entry = {
            "type": p.type,
            "status": p.status,
            "created_at": p.created_at.isoformat() if hasattr(p, 'created_at') else None,
        }
        role = get_role_for_pheromone_type(p.type)
        entry["handled_by"] = ROLE_NAMES.get(role, "System") if role else "System"
        if p.medication_name:
            entry["medication_name"] = p.medication_name
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
            entry["escalated_from"] = p.escalated_from
        timeline_entries.append(entry)

    result = {
        "patient_id": patient.patient_id,
        "condition": patient.condition,
        "severity": patient.severity,
        "status": patient.status,
        "acuity": "",
        "vitals": {
            "heart_rate": patient.heart_rate,
            "bp_systolic": patient.bp_systolic,
            "bp_diastolic": patient.bp_diastolic,
            "o2_saturation": patient.o2_saturation,
            "temperature": patient.temperature,
        },
        "current_step": current,
        "next_step": next_step,
        "active_tasks": active_tasks,
        "timeline": timeline_entries,
    }

    # Determine patient's current acuity from active tasks
    if current and current.get("acuity"):
        result["acuity"] = current["acuity"]
    elif active_tasks:
        acuities = [t.get("acuity", "") for t in active_tasks if t.get("acuity")]
        if acuities:
            result["acuity"] = acuities[0]

    return result


@router.get("/{patient_id}/report", response_class=HTMLResponse)
async def get_patient_report(patient_id: str):
    p_service = PatientService()
    ph_service = PheromoneService()

    patient = await p_service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    all_pheromones = await ph_service.get_pheromones_for_patient(patient_id)
    sorted_pheromones = sorted(all_pheromones, key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.min)

    condition_label = patient.condition.replace("_", " ").title()
    severity_label = "Critical" if patient.severity > 0.7 else "Moderate" if patient.severity > 0.4 else "Stable"

    rows_html = ""
    for p in sorted_pheromones:
        role = get_role_for_pheromone_type(p.type)
        handled_by = ROLE_NAMES.get(role, "System") if role else "System"
        icon = ROLE_ICONS.get(role, "📌") if role else "📌"
        created = p.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(p, 'created_at') and p.created_at else "N/A"
        status_badge = "🟢 Active" if p.status == "active" else "✅ Completed"

        details = ""
        if p.medication_name:
            details += f"<tr><td style='padding:4px 8px;color:#666;'>Medication</td><td style='padding:4px 8px;'><strong>{h(p.medication_name)}</strong> — {h(p.medication_dosage)}</td></tr>"
        if p.test_type:
            details += f"<tr><td style='padding:4px 8px;color:#666;'>Test</td><td style='padding:4px 8px;'><strong>{h(p.test_type)}</strong></td></tr>"
        if p.test_result:
            details += f"<tr><td style='padding:4px 8px;color:#666;'>Result</td><td style='padding:4px 8px;'><strong>{h(p.test_result)}</strong></td></tr>"
        if p.sbar_situation:
            details += f"<tr><td style='padding:4px 8px;color:#666;'>Notes</td><td style='padding:4px 8px;'>{h(p.sbar_situation)}</td></tr>"
        if p.sbar_assessment:
            details += f"<tr><td style='padding:4px 8px;color:#666;'>Assessment</td><td style='padding:4px 8px;'>{h(p.sbar_assessment)}</td></tr>"
        if p.sbar_recommendation:
            details += f"<tr><td style='padding:4px 8px;color:#666;'>Recommendation</td><td style='padding:4px 8px;'>{h(p.sbar_recommendation)}</td></tr>"

        rows_html += f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px 12px;text-align:center;font-size:20px;">{icon}</td>
            <td style="padding:10px 12px;"><strong>{h(p.type)}</strong><br><span style="font-size:12px;color:#666;">by {h(handled_by)}</span></td>
            <td style="padding:10px 12px;">{h(status_badge)}</td>
            <td style="padding:10px 12px;font-size:13px;color:#666;">{h(created)}</td>
        </tr>
        {('<tr><td colspan="4" style="padding:0 12px 8px 50px;font-size:13px;"><table>' + details + '</table></td></tr>') if details else ''}
        """

    prescriptions = [p for p in sorted_pheromones if p.type == "PRESCRIPTION" and p.medication_name]
    lab_results = [p for p in sorted_pheromones if p.type in ("LAB_REQUEST", "LAB_COMPLETE") and (p.test_type or p.test_result)]

    vitals_str = f"HR: {patient.heart_rate or 'N/A'} | BP: {patient.bp_systolic or 'N/A'}/{patient.bp_diastolic or 'N/A'} | O2: {patient.o2_saturation or 'N/A'}% | Temp: {patient.temperature or 'N/A'}°C"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Patient Report - {h(patient_id)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
  .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #1976d2; margin-bottom: 20px; }}
  .header h1 {{ margin: 0; font-size: 24px; color: #1976d2; }}
  .header p {{ margin: 4px 0 0; color: #666; font-size: 14px; }}
  .section {{ margin-bottom: 24px; }}
  .section h2 {{ font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 6px; margin: 0 0 12px; color: #333; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; font-size: 14px; }}
  .info-grid .label {{ color: #666; }}
  .info-grid .value {{ font-weight: 500; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th {{ text-align: left; padding: 8px 12px; background: #f5f5f5; font-size: 12px; text-transform: uppercase; color: #666; }}
  .footer {{ text-align: center; margin-top: 30px; padding-top: 16px; border-top: 1px solid #eee; font-size: 12px; color: #999; }}
  @media print {{ body {{ padding: 0; }} .no-print {{ display: none; }} }}
</style></head>
<body>
<div class="header">
    <h1>🏥 Patient Medical Report</h1>
    <p>Stigmergic Hospital Swarm OS — Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
</div>

<div class="section">
    <h2>Patient Information</h2>
    <div class="info-grid">
        <div><span class="label">Patient ID:</span> <span class="value">{h(patient_id)}</span></div>
        <div><span class="label">Condition:</span> <span class="value">{h(condition_label)}</span></div>
        <div><span class="label">Severity:</span> <span class="value">{h(severity_label)} ({patient.severity:.2f})</span></div>
        <div><span class="label">Status:</span> <span class="value">{h(patient.status.title())}</span></div>
        <div><span class="label">Current Vitals:</span> <span class="value">{h(vitals_str)}</span></div>
    </div>
</div>

<div class="section">
    <h2>💊 Prescribed Medications</h2>
    {f'<table><tr><th>Medication</th><th>Dosage</th><th>Status</th></tr>' + ''.join(f'<tr><td style="padding:8px 12px;">{h(p.medication_name)}</td><td style="padding:8px 12px;">{h(p.medication_dosage)}</td><td style="padding:8px 12px;">{h(p.status.title())}</td></tr>' for p in prescriptions) + '</table>' if prescriptions else '<p style="color:#999;">No medications prescribed</p>'}
</div>

<div class="section">
    <h2>🔬 Lab Reports</h2>
    {f'<table><tr><th>Test</th><th>Result</th><th>Status</th></tr>' + ''.join(f'<tr><td style="padding:8px 12px;">{h(p.test_type or "—")}</td><td style="padding:8px 12px;">{h(p.test_result or "Pending")}</td><td style="padding:8px 12px;">{h(p.status.title())}</td></tr>' for p in lab_results) + '</table>' if lab_results else '<p style="color:#999;">No lab tests performed</p>'}
</div>

<div class="section">
    <h2>📋 Clinical Notes (SBAR)</h2>
    {f'<table><tr><th>Stage</th><th>Situation</th><th>Assessment</th><th>Recommendation</th></tr>' + ''.join(f'<tr><td style="padding:8px 12px;">{h(p.type)}</td><td style="padding:8px 12px;">{h(p.sbar_situation or "—")}</td><td style="padding:8px 12px;">{h(p.sbar_assessment or "—")}</td><td style="padding:8px 12px;">{h(p.sbar_recommendation or "—")}</td></tr>' for p in sorted_pheromones if p.sbar_situation) + '</table>' if any(p.sbar_situation for p in sorted_pheromones) else '<p style="color:#999;">No clinical notes</p>'}
</div>

<div class="section">
    <h2>📜 Full Event Timeline</h2>
    <table>
        <tr><th style="width:50px;"></th><th>Event</th><th style="width:100px;">Status</th><th style="width:160px;">Time</th></tr>
        {rows_html}
    </table>
</div>

<div class="section no-print">
    <h2>Diagnosis Summary</h2>
    <div style="background:#f9f9f9;border-radius:8px;padding:16px;font-size:14px;line-height:1.6;">
        <p><strong>Final Diagnosis:</strong> {h(condition_label)}</p>
        <p><strong>Severity at Admission:</strong> {h(severity_label)} ({patient.severity:.2f})</p>
        <p><strong>Medications Administered:</strong> {len(prescriptions)} medication(s) prescribed</p>
        <p><strong>Tests Conducted:</strong> {len(lab_results)} test(s) performed</p>
        <p><strong>Current Status:</strong> {h(patient.status.title())}</p>
    </div>
</div>

<div class="footer">
    <p>This is a computer-generated report from the Stigmergic Hospital Swarm OS.</p>
    <p>Report ID: RPT-{h(patient_id)}-{datetime.now().strftime("%Y%m%d%H%M%S")}</p>
</div>
</body></html>"""

    return HTMLResponse(content=html, status_code=200)
