from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import asyncio

from .database import create_tables, get_db, ServiceHealthDB, CrashReportDB, QAChecklistDB
from .schemas import ServiceHealth, CrashReport, ReleaseCheckitem, TelemetryData
from .telemetry import telemetry_manager

app = FastAPI(
    title="VroomPulse Telemetry Hub",
    description="Operational monitoring, crash triaging, and release QA pipeline for Vroom infrastructure.",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'HTTP request latency')

# Initialize database and seed data
def seed_database(db: Session):
    if db.query(ServiceHealthDB).count() == 0:
        services = [
            ServiceHealthDB(service_name="Auth Service (Firebase)", status="healthy", latency_ms=42.5, last_check=datetime.utcnow()),
            ServiceHealthDB(service_name="Ride Matcher Engine (AWS EC2)", status="healthy", latency_ms=18.2, last_check=datetime.utcnow()),
            ServiceHealthDB(service_name="Payment Gateway Webhook", status="healthy", latency_ms=95.0, last_check=datetime.utcnow()),
        ]
        db.add_all(services)
        
        crashes = [
            CrashReportDB(platform="Android", app_version="1.2.0", error_message="NullPointerException on Driver Location Update", impacted_users=45, severity="Critical", timestamp=datetime.utcnow()),
            CrashReportDB(platform="iOS", app_version="1.1.9", error_message="EXC_BAD_ACCESS in Socket Connection", impacted_users=12, severity="Medium", timestamp=datetime.utcnow()),
        ]
        db.add_all(crashes)
        
        qa_items = [
            QAChecklistDB(task="App Store / Play Store API SSL Pinning verified", passed=True, owner="DevOps"),
            QAChecklistDB(task="Expo/EAS Production Build Sign-off", passed=True, owner="Mobile Team"),
            QAChecklistDB(task="Database Failover Backup Sync", passed=True, owner="IT Admin"),
            QAChecklistDB(task="Firebase Auth Token Expiration Test", passed=False, owner="QA Lead"),
        ]
        db.add_all(qa_items)
        
        db.commit()

@app.on_event("startup")
async def startup_event():
    create_tables()
    db = next(get_db())
    seed_database(db)
    # Start telemetry simulation in the background
    asyncio.create_task(telemetry_manager.simulate_telemetry(db))

@app.middleware("http")
async def metrics_middleware(request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.observe(process_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    telemetry_manager.add_subscriber(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        telemetry_manager.remove_subscriber(websocket)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/api/v1/dashboard", response_model=TelemetryData)
async def get_dashboard(db: Session = Depends(get_db)):
    services = db.query(ServiceHealthDB).all()
    crashes = db.query(CrashReportDB).all()
    qa_items = db.query(QAChecklistDB).all()
    
    return TelemetryData(
        services=[ServiceHealth(
            service_name=s.service_name,
            status=s.status,
            latency_ms=round(s.latency_ms, 1),
            last_check=s.last_check.isoformat()
        ) for s in services],
        crashes=[CrashReport(
            id=c.id,
            platform=c.platform,
            app_version=c.app_version,
            error_message=c.error_message,
            impacted_users=c.impacted_users,
            severity=c.severity,
            timestamp=c.timestamp.isoformat() if c.timestamp else None
        ) for c in crashes],
        qa_checklist=[ReleaseCheckitem(
            id=q.id,
            task=q.task,
            passed=q.passed,
            owner=q.owner
        ) for q in qa_items],
        metrics={
            "total_requests": 1247,
            "avg_latency": round(sum(s.latency_ms for s in services) / len(services), 1) if services else 0,
            "error_rate": 0.02
        }
    )

@app.get("/api/v1/healthcheck", response_model=List[ServiceHealth])
async def get_service_health(db: Session = Depends(get_db)):
    services = db.query(ServiceHealthDB).all()
    return [ServiceHealth(
        service_name=s.service_name,
        status=s.status,
        latency_ms=round(s.latency_ms, 1),
        last_check=s.last_check.isoformat()
    ) for s in services]

@app.get("/api/v1/crashes", response_model=List[CrashReport])
async def get_crash_reports(db: Session = Depends(get_db)):
    crashes = db.query(CrashReportDB).all()
    return sorted([CrashReport(
        id=c.id,
        platform=c.platform,
        app_version=c.app_version,
        error_message=c.error_message,
        impacted_users=c.impacted_users,
        severity=c.severity,
        timestamp=c.timestamp.isoformat() if c.timestamp else None
    ) for c in crashes], key=lambda x: x.impacted_users, reverse=True)

@app.get("/api/v1/qa-checklist", response_model=List[ReleaseCheckitem])
async def get_qa_checklist(db: Session = Depends(get_db)):
    qa_items = db.query(QAChecklistDB).all()
    return [ReleaseCheckitem(
        id=q.id,
        task=q.task,
        passed=q.passed,
        owner=q.owner
    ) for q in qa_items]

@app.post("/api/v1/qa-checklist/{item_id}/toggle")
async def toggle_qa_item(item_id: int, db: Session = Depends(get_db)):
    qa_item = db.query(QAChecklistDB).filter(QAChecklistDB.id == item_id).first()
    if not qa_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    qa_item.passed = not qa_item.passed
    db.commit()
    
    return {"status": "success", "item": ReleaseCheckitem(
        id=qa_item.id,
        task=qa_item.task,
        passed=qa_item.passed,
        owner=qa_item.owner
    )}
