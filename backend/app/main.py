from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.database import SessionLocal, engine
from app.models import Payment, RecoveryAttempt
from app.services.recovery_service import RecoveryService


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


@app.get("/api/recovery")
def get_recovery_queue():
    db = SessionLocal()

    try:
        payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .order_by(Payment.id)
            .all()
        )

        results = []

        for payment in payments:
            strategy = RecoveryService.determine_strategy(payment)

            results.append({
                "payment_id": payment.id,
                "customer": {
                    "id": payment.customer.id,
                    "name": payment.customer.name,
                    "email": payment.customer.email,
                },
                "payment_status": payment.status,
                "failure_reason": payment.failure_reason,
                "amount": float(payment.amount),
                "currency": payment.currency,
                "due_date": payment.due_date,
                "recovery": strategy,
            })

        return {
            "count": len(results),
            "payments": results,
        }

    finally:
        db.close()


@app.get("/api/recovery/{payment_id}")
def get_recovery_strategy(payment_id: int):
    db = SessionLocal()

    try:
        payment = db.get(Payment, payment_id)

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        strategy = RecoveryService.determine_strategy(payment)

        existing_attempt = (
            db.query(RecoveryAttempt)
            .filter(RecoveryAttempt.payment_id == payment.id)
            .first()
        )

        if existing_attempt:
            recovery_attempt = existing_attempt

        else:
            recovery_attempt = RecoveryAttempt(
                payment_id=payment.id,
                channel="system",
                strategy=strategy["action"],
                message=strategy["message"],
                status="pending",
            )

            db.add(recovery_attempt)
            db.commit()
            db.refresh(recovery_attempt)

        return {
            "payment_id": payment.id,
            "payment_status": payment.status,
            "failure_reason": payment.failure_reason,
            "recovery": strategy,
            "recovery_attempt": {
                "id": recovery_attempt.id,
                "channel": recovery_attempt.channel,
                "status": recovery_attempt.status,
                "attempted_at": recovery_attempt.attempted_at,
            },
        }

    finally:
        db.close()