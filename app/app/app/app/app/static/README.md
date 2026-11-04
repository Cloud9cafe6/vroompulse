# VroomPulse Telemetry Hub v2.0

**Production-Ready Infrastructure Monitoring for ApaNiVroom**

## 🚀 Features

- **Real-Time Monitoring**: WebSocket-based live telemetry updates
- **Persistent Storage**: SQLite database for crash reports and service health
- **Prometheus Metrics**: Professional-grade metrics endpoint for monitoring
- **QA Pipeline**: Interactive release checklist management
- **Crash Triage**: Prioritized crash reporting with impact analysis
- **Docker Ready**: Containerized deployment with Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- Prometheus (optional, for metrics visualization)

## 🛠️ Installation

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/vroompulse.git
cd vroompulse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
