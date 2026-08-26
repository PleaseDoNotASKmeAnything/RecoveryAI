from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine


app = FastAPI(
    title="RecoveryAI API",
    description="AI-powered revenue recovery platform",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "RecoveryAI API is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "RecoveryAI",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error),
        }