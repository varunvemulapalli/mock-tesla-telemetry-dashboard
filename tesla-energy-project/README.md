# Tesla Energy Device Software - Powerwall Telemetry Dashboard

A simulation of Tesla's Energy Device Software platform demonstrating real-time telemetry visualization, device control, and AI-powered health analysis for residential energy products.

## Overview

This project simulates an Energy Device Software platform for Tesla's residential energy products (Powerwall, Solar Inverter, Wall Connector). It showcases full-stack capabilities for installation, configuration, diagnosis, and monitoring of distributed energy systems.

Built with: Python (FastAPI), React (TypeScript), Plotly, OpenAI GPT, WebSockets

## Features

- Real-time telemetry dashboard with live visualization
- Multi-device fleet management
- Device control panel (Charge Now, Isolate from Grid, Reboot, Firmware Update)
- AI-powered health analysis using GPT
- Historical data analytics with time-series analysis
- WebSocket real-time updates
- RESTful API for integration

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key (for GPT features)

### Installation

1. Clone the repository
   ```bash
   git clone <your-repo-url>
   cd tesla-energy-project
   ```

2. Backend Setup
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. Frontend Setup
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   ```

4. Start Services
   ```bash
   # Run start script
   ./start.sh
   ```

   Or manually:
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn app.main:app --reload --port 8000

   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

5. Access Dashboard
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - API Health: http://localhost:8000/health

## Project Structure

```
tesla-energy-project/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── device.py
│   │   │   └── telemetry.py
│   │   ├── api/
│   │   │   ├── devices.py
│   │   │   ├── telemetry.py
│   │   │   ├── control.py
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── data_simulator.py
│   │   │   ├── device_manager.py
│   │   │   ├── gpt_service.py
│   │   │   └── websocket_manager.py
│   │   └── utils/
│   │       └── analytics.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   ├── ControlPanel/
│   │   │   ├── HealthAnalysis/
│   │   │   ├── DeviceList/
│   │   │   └── Charts/
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   └── types/
│   │       └── device.ts
│   └── package.json
└── README.md
```

## Configuration

### Environment Variables

**Backend (.env)**
```env
OPENAI_API_KEY=your_openai_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
SIMULATOR_ENABLED=true
```

**Frontend (.env)**
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## API Documentation

### Device Endpoints
- `GET /api/devices` - List all devices
- `GET /api/devices/{device_id}` - Get device details
- `POST /api/devices` - Register new device
- `PUT /api/devices/{device_id}/config` - Update device configuration

### Telemetry Endpoints
- `GET /api/telemetry/{device_id}` - Get latest telemetry
- `GET /api/telemetry/{device_id}/history` - Get historical data
- `WebSocket /ws/{device_id}` - Real-time telemetry stream

### Control Endpoints
- `POST /api/control/{device_id}` - Execute control command
- `GET /api/devices/{device_id}/status` - Get device status

### Health Analysis
- `POST /api/health/analyze` - AI-powered system health analysis

Full API documentation available at `/docs` when the backend is running.

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Notes

This is a simulation project inspired by Tesla Energy's configuration and monitoring tools. All telemetry data is generated programmatically and does not connect to real Tesla devices. The architecture and implementation patterns demonstrate production-ready software engineering practices for IoT and energy management systems.
