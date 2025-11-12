import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio

from app.api import devices, telemetry, control, health
from app.services.data_simulator import simulator

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Tesla Energy Device Software API...")
    
    simulator_enabled = os.getenv("SIMULATOR_ENABLED", "true").lower() == "true"
    if simulator_enabled:
        simulator_task = asyncio.create_task(simulator.run(interval_seconds=5.0))
        print("Data simulator started")
    else:
        simulator_task = None
    
    yield
    
    print("Shutting down...")
    if simulator_task:
        simulator.stop()
        simulator_task.cancel()
        try:
            await simulator_task
        except asyncio.CancelledError:
            pass
    print("Shutdown complete")


app = FastAPI(
    title="Tesla Energy Device Software API",
    description="API for monitoring and controlling Tesla Energy residential devices",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(control.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {
        "name": "Tesla Energy Device Software API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "tesla-energy-api",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
    )

