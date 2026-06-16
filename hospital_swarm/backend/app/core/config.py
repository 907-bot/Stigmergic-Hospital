from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    PROJECT_NAME: str = "Stigmergic Hospital Swarm OS"
    API_V1_STR: str = "/api/v1"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3002",
        "http://localhost:8000",
    ]

    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="password")

    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)

    # --- SaaS / Auth ---
    SECRET_KEY: str = Field(default="change-me-in-production-please")
    ALGORITHM: str = "HS256"
    OKTA_DOMAIN: str | None = Field(default=None)
    OKTA_CLIENT_ID: str | None = Field(default=None)
    OKTA_CLIENT_SECRET: str | None = Field(default=None)
    AZURE_TENANT_ID: str | None = Field(default=None)
    AZURE_CLIENT_ID: str | None = Field(default=None)

    # --- HIPAA / Audit ---
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=365 * 6)
    PHI_ENCRYPTION_KEY: str = Field(default="")

    # --- FHIR ---
    FHIR_BASE_URL: str = Field(default="/fhir/r4")
    FHIR_PAGE_SIZE: int = 50

    # --- Multi-tenant ---
    ENABLE_MULTI_TENANT: bool = Field(default=False)


settings = Settings()
