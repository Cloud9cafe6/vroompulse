import asyncio
import random
from datetime import datetime
from sqlalchemy.orm import Session

from .database import ServiceHealthDB, CrashReportDB, QAChecklistDB
from .schemas import ServiceHealth, CrashReport, ReleaseCheckitem

class TelemetryManager:
    def __init__(self):
        self.subscribers = set()
    
    def add_subscriber(self, websocket):
        self.subscribers.add(websocket)
    
    def remove_subscriber(self, websocket):
        self.subscribers.discard(websocket)
    
    async def broadcast(self, message: dict):
        if self.subscribers:
            await asyncio.gather(
                *[subscriber.send_json(message) for subscriber in self.subscribers],
                return_exceptions=True
            )
    
    async def simulate_telemetry(self, db: Session):
        """Simulate real-time telemetry updates and broadcast to clients"""
        while True:
            try:
                # Update service health with realistic variations
                services = db.query(ServiceHealthDB).all()
                for service in services:
                    # Simulate latency fluctuations
                    base_latency = service.latency_ms
                    variation = random.uniform(-5, 15)
                    service.latency_ms = max(5, base_latency + variation)
                    service.last_check = datetime.utcnow()
                    
                    # Simulate occasional degradation (5% chance)
                    if random.random() < 0.05:
                        service.status = random.choice(['healthy', 'degraded', 'healthy', 'healthy'])
                
                db.commit()
                
                # Get updated data for broadcast
                services_data = [
                    ServiceHealth(
                        service_name=s.service_name,
                        status=s.status,
                        latency_ms=round(s.latency_ms, 1),
                        last_check=s.last_check.isoformat()
                    ) for s in services
                ]
                
                crashes_data = [
                    CrashReport(
                        id=c.id,
                        platform=c.platform,
                        app_version=c.app_version,
                        error_message=c.error_message,
                        impacted_users=c.impacted_users,
                        severity=c.severity,
                        timestamp=c.timestamp.isoformat() if c.timestamp else None
                    ) for c in db.query(CrashReportDB).all()
                ]
                
                qa_data = [
                    ReleaseCheckitem(
                        id=q.id,
                        task=q.task,
                        passed=q.passed,
                        owner=q.owner
                    ) for q in db.query(QAChecklistDB).all()
                ]
                
                # Broadcast to all connected WebSocket clients
                await self.broadcast({
                    "services": services_data,
                    "crashes": crashes_data,
                    "qa_checklist": qa_data,
                    "metrics": {
                        "total_requests": random.randint(1000, 2000),
                        "avg_latency": round(sum(s.latency_ms for s in services_data) / len(services_data), 1) if services_data else 0,
                        "error_rate": round(random.uniform(0.01, 0.05), 2)
                    }
                })
                
                # Update every 5 seconds
                await asyncio.sleep(5) 
                
            except Exception as e:
                print(f"Telemetry simulation error: {e}")
                await asyncio.sleep(5)

# Global instance
telemetry_manager = TelemetryManager()
