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


@app.get("/api/recovery/stats")
def get_recovery_stats():
    db = SessionLocal()

    try:
        failed_payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .all()
        )

        paid_payments = (
            db.query(Payment)
            .filter(Payment.status == "paid")
            .all()
        )

        total_failed_amount = sum(
            float(payment.amount)
            for payment in failed_payments
        )

        total_paid_amount = sum(
            float(payment.amount)
            for payment in paid_payments
        )

        total_payments = len(failed_payments) + len(paid_payments)

        recovery_rate = (
            (len(paid_payments) / total_payments) * 100
            if total_payments > 0
            else 0
        )

        affected_customers = len({
            payment.customer_id
            for payment in failed_payments
        })

        priority_counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for payment in failed_payments:
            strategy = RecoveryService.determine_strategy(payment)
            priority = strategy["priority"]

            if priority in priority_counts:
                priority_counts[priority] += 1

        return {
            "failed_payments": len(failed_payments),
            "total_failed_amount": total_failed_amount,
            "paid_payments": len(paid_payments),
            "total_paid_amount": total_paid_amount,
            "recovery_rate": round(recovery_rate, 2),
            "affected_customers": affected_customers,
            "currency": "USD",
            "priority": priority_counts,
        }

    finally:
        db.close()


@app.get("/api/recovery/attempts")
def get_recovery_attempts():
    db = SessionLocal()

    try:
        attempts = (
            db.query(RecoveryAttempt)
            .order_by(RecoveryAttempt.id)
            .all()
        )

        results = []

        for attempt in attempts:
            payment = attempt.payment

            results.append({
                "attempt_id": attempt.id,
                "payment_id": attempt.payment_id,
                "customer": {
                    "id": payment.customer.id,
                    "name": payment.customer.name,
                    "email": payment.customer.email,
                },
                "strategy": attempt.strategy,
                "channel": attempt.channel,
                "message": attempt.message,
                "status": attempt.status,
                "attempted_at": attempt.attempted_at,
            })

        return {
            "count": len(results),
            "attempts": results,
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