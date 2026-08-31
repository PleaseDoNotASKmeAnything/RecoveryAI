from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from app.database import SessionLocal, engine
from app.models import Payment, RecoveryAttempt
from app.services.recovery_service import RecoveryService


class RecoveryAttemptUpdate(BaseModel):
    status: str


app = FastAPI(
    title="RecoveryAI API",
    description="AI-powered revenue recovery platform",
    version="0.1.0",
)


# Allow the React frontend to communicate with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
def get_recovery_queue(
    priority: str | None = None,
    failure_reason: str | None = None,
):
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

            if priority and strategy["priority"] != priority:
                continue

            if (
                failure_reason
                and payment.failure_reason != failure_reason
            ):
                continue

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


@app.get("/api/recovery/analytics")
def get_recovery_analytics():
    db = SessionLocal()

    try:
        attempts = (
            db.query(RecoveryAttempt)
            .order_by(RecoveryAttempt.id)
            .all()
        )

        total_attempts = len(attempts)

        successful_attempts = sum(
            1
            for attempt in attempts
            if attempt.status in {"sent", "completed"}
        )

        failed_attempts = sum(
            1
            for attempt in attempts
            if attempt.status == "failed"
        )

        pending_attempts = sum(
            1
            for attempt in attempts
            if attempt.status == "pending"
        )

        success_rate = (
            (successful_attempts / total_attempts) * 100
            if total_attempts > 0
            else 0
        )

        strategy_counts = {}

        for attempt in attempts:
            strategy = attempt.strategy

            if strategy not in strategy_counts:
                strategy_counts[strategy] = 0

            strategy_counts[strategy] += 1

        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "pending_attempts": pending_attempts,
            "success_rate": round(success_rate, 2),
            "strategy_breakdown": strategy_counts,
        }

    finally:
        db.close()


@app.post("/api/recovery/attempts/{payment_id}")
def create_recovery_attempt(payment_id: int):
    db = SessionLocal()

    try:
        payment = db.get(Payment, payment_id)

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        if payment.status != "failed":
            raise HTTPException(
                status_code=400,
                detail="Recovery attempts can only be created for failed payments",
            )

        strategy = RecoveryService.determine_strategy(payment)

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
            "message": "Recovery attempt created successfully",
            "attempt": {
                "id": recovery_attempt.id,
                "payment_id": recovery_attempt.payment_id,
                "channel": recovery_attempt.channel,
                "strategy": recovery_attempt.strategy,
                "message": recovery_attempt.message,
                "status": recovery_attempt.status,
                "attempted_at": recovery_attempt.attempted_at,
            },
        }

    finally:
        db.close()


@app.patch("/api/recovery/attempts/{attempt_id}")
def update_recovery_attempt(
    attempt_id: int,
    update: RecoveryAttemptUpdate,
):
    db = SessionLocal()

    try:
        attempt = db.get(RecoveryAttempt, attempt_id)

        if not attempt:
            raise HTTPException(
                status_code=404,
                detail="Recovery attempt not found",
            )

        allowed_statuses = {
            "pending",
            "sent",
            "completed",
            "failed",
        }

        if update.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid recovery attempt status",
                    "allowed_statuses": list(allowed_statuses),
                },
            )

        attempt.status = update.status

        db.commit()
        db.refresh(attempt)

        return {
            "message": "Recovery attempt updated successfully",
            "attempt": {
                "id": attempt.id,
                "payment_id": attempt.payment_id,
                "channel": attempt.channel,
                "strategy": attempt.strategy,
                "message": attempt.message,
                "status": attempt.status,
                "attempted_at": attempt.attempted_at,
            },
        }

    finally:
        db.close()


@app.post("/api/recovery/attempts/{attempt_id}/execute")
def execute_recovery_attempt(attempt_id: int):
    db = SessionLocal()

    try:
        attempt = db.get(RecoveryAttempt, attempt_id)

        if not attempt:
            raise HTTPException(
                status_code=404,
                detail="Recovery attempt not found",
            )

        if attempt.status == "completed":
            raise HTTPException(
                status_code=400,
                detail="Recovery attempt has already been completed",
            )

        if attempt.status == "failed":
            raise HTTPException(
                status_code=400,
                detail="Recovery attempt has already failed",
            )

        # Count previous recovery attempts for the same payment.
        previous_attempts = (
            db.query(RecoveryAttempt)
            .filter(
                RecoveryAttempt.payment_id == attempt.payment_id,
                RecoveryAttempt.id != attempt.id,
            )
            .count()
        )

        execution = RecoveryService.execute_strategy(
            attempt,
            previous_attempts,
        )

        if execution["success"]:
            attempt.status = "sent"

            db.commit()
            db.refresh(attempt)

            return {
                "message": "Recovery attempt executed successfully",
                "execution": execution,
                "attempt": {
                    "id": attempt.id,
                    "payment_id": attempt.payment_id,
                    "channel": attempt.channel,
                    "strategy": attempt.strategy,
                    "status": attempt.status,
                    "attempted_at": attempt.attempted_at,
                },
            }

        # Retry limit reached.
        attempt.status = "failed"

        db.commit()
        db.refresh(attempt)

        return {
            "message": "Recovery attempt blocked by retry limit",
            "execution": execution,
            "attempt": {
                "id": attempt.id,
                "payment_id": attempt.payment_id,
                "channel": attempt.channel,
                "strategy": attempt.strategy,
                "status": attempt.status,
                "attempted_at": attempt.attempted_at,
            },
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