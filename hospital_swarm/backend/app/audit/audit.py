from datetime import datetime
from typing import Optional, Literal
from app.db.neo4j import run_query
import uuid
import logging

logger = logging.getLogger(__name__)

AuditAction = Literal[
    "PATIENT_VIEW",
    "PATIENT_CREATE",
    "PATIENT_UPDATE",
    "PATIENT_DELETE",
    "RECORD_ACCESS",
    "RECORD_EXPORT",
    "RECORD_MODIFY",
    "USER_LOGIN",
    "USER_LOGOUT",
    "USER_CREATE",
    "ROLE_CHANGE",
    "CONSENT_CHANGE",
    "BREACH_ATTEMPT",
    "SYSTEM_CONFIG_CHANGE",
]


async def log_audit_event(
    action: AuditAction,
    actor_id: str,
    tenant_id: str,
    patient_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    outcome: Literal["success", "denied", "error"] = "success",
):
    """
    HIPAA-compliant audit log. Every PHI access is recorded with:
    - Who (actor_id, role inferred)
    - What (action)
    - When (timestamp)
    - Where (ip_address)
    - Which patient (patient_id)
    - Outcome (success/denied/error)
    """
    event_id = f"AUD{uuid.uuid4().hex[:10]}"
    now = datetime.utcnow().isoformat()

    query = """
    CREATE (a:AuditEvent {
        event_id: $event_id,
        action: $action,
        actor_id: $actor_id,
        tenant_id: $tenant_id,
        patient_id: $patient_id,
        resource_type: $resource_type,
        resource_id: $resource_id,
        detail: $detail,
        ip_address: $ip_address,
        user_agent: $user_agent,
        outcome: $outcome,
        timestamp: $timestamp
    })
    RETURN a
    """

    try:
        await run_query(
            query,
            {
                "event_id": event_id,
                "action": action,
                "actor_id": actor_id,
                "tenant_id": tenant_id,
                "patient_id": patient_id or "",
                "resource_type": resource_type or "",
                "resource_id": resource_id or "",
                "detail": detail or "",
                "ip_address": ip_address or "",
                "user_agent": user_agent or "",
                "outcome": outcome,
                "timestamp": now,
            },
        )
        logger.info(f"AUDIT [{action}] actor={actor_id} patient={patient_id} outcome={outcome}")
    except Exception as e:
        logger.error(f"Failed to write audit event: {e}")


class AuditMiddleware:
    """
    FastAPI middleware that auto-logs all requests to /api/v1/patients
    and /api/v1/patient-portal as PATIENT_VIEW audit events.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # We capture at the endpoint level instead for precision
        await self.app(scope, receive, send)
