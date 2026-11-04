from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# --- Pydantic Schemas (API Data Models) ---

class ServiceHealth(BaseModel):
    service_name: str
    status: str  # healthy, degraded, offline
    latency_ms: float
    last_check: str

class CrashReport(BaseModel):
    id: int
    platform: str  # iOS / Android
    app_version: str
    error_message: str
    impacted_users: int
    severity: str  # Low, Medium, Critical
    timestamp: Optional[str] = None

class ReleaseCheckitem(BaseModel):
    id: int
    task: str
    passed: bool
    owner: str

class TelemetryData(BaseModel):
    services: list[ServiceHealth]
    crashes: list[CrashReport]
    qa_checklist: list[ReleaseCheckitem]
    metrics: dict
