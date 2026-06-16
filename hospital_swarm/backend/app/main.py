import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.api.v1.router import api_router
from app.auth.routes import router as auth_router
from app.fhir.router import router as fhir_router
from app.core.config import settings
from app.services.simulation_service import SimulationService
from app.db.neo4j import init_neo4j, close_neo4j, ensure_indexes
from app.tenants.middleware import resolve_tenant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing Neo4j connection pool")
    await init_neo4j()
    await ensure_indexes()

    simulation_service = SimulationService()
    app.state.simulation_service = simulation_service

    yield

    logger.info("Shutting down — stopping simulation and closing connections")
    if simulation_service._is_running:
        await simulation_service.stop_simulation()
    await close_neo4j()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    Stigmergic Hospital Swarm OS — Multi-tenant SaaS for hospital coordination.
    
    ## SaaS Features
    * **JWT Auth** with Okta/Azure AD integration
    * **HIPAA Audit Trail** — every PHI access logged
    * **FHIR R4 API** — HL7 FHIR Release 4 compliant endpoints
    * **Multi-tenant** — complete data isolation between hospitals
    * **Role-based access** — admin, clinician, nurse, doctor, lab, etc.
    """,
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    contact={
        "name": "Hospital Swarm Team",
        "url": "https://hospital-swarm.example.com",
    },
    license_info={
        "name": "Enterprise License",
    },
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    tenant_id = await resolve_tenant(request)
    request.state.tenant_id = tenant_id or "default"
    response = await call_next(request)
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(fhir_router, prefix="/fhir/r4", tags=["fhir"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to Stigmergic Hospital Swarm OS",
        "version": "2.0.0",
        "docs": "/docs",
        "fhir": "/fhir/r4/metadata",
        "status": "SaaS-ready with Auth, HIPAA audit, FHIR R4, multi-tenant",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "mode": "saas"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
