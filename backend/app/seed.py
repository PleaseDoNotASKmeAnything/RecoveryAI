from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Customer, Subscription, Payment


def seed_database():
    db = SessionLocal()

    try:
        existing_customer = db.scalar(
            select(Customer).limit(1)
        )

        if existing_customer:
            print("Database already contains data.")
            print("Skipping seed operation.")
            return

        now = datetime.utcnow()

        customers = [
            Customer(
                name="Aarav Sharma",
                email="aarav@example.com",
            ),
            Customer(
                name="Priya Mehta",
                email="priya@example.com",
            ),
            Customer(
                name="Rohan Verma",
                email="rohan@example.com",
            ),
            Customer(
                name="Ananya Kapoor",
                email="ananya@example.com",
            ),
            Customer(
                name="Vikram Singh",
                email="vikram@example.com",
            ),
            Customer(
                name="Ishita Gupta",
                email="ishita@example.com",
            ),
            Customer(
                name="Arjun Malhotra",
                email="arjun@example.com",
            ),
            Customer(
                name="Meera Joshi",
                email="meera@example.com",
            ),
        ]

        db.add_all(customers)
        db.flush()

        subscriptions = [
            Subscription(
                customer_id=customers[0].id,
                plan_name="Pro",
                amount=49.00,
                status="active",
                started_at=now - timedelta(days=180),
            ),
            Subscription(
                customer_id=customers[1].id,
                plan_name="Business",
                amount=99.00,
                status="active",
                started_at=now - timedelta(days=150),
            ),
            Subscription(
                customer_id=customers[2].id,
                plan_name="Pro",
                amount=49.00,
                status="active",
                started_at=now - timedelta(days=120),
            ),
            Subscription(
                customer_id=customers[3].id,
                plan_name="Starter",
                amount=19.00,
                status="active",
                started_at=now - timedelta(days=90),
            ),
            Subscription(
                customer_id=customers[4].id,
                plan_name="Business",
                amount=99.00,
                status="active",
                started_at=now - timedelta(days=240),
            ),
            Subscription(
                customer_id=customers[5].id,
                plan_name="Pro",
                amount=49.00,
                status="active",
                started_at=now - timedelta(days=200),
            ),
            Subscription(
                customer_id=customers[6].id,
                plan_name="Starter",
                amount=19.00,
                status="active",
                started_at=now - timedelta(days=60),
            ),
            Subscription(
                customer_id=customers[7].id,
                plan_name="Pro",
                amount=49.00,
                status="active",
                started_at=now - timedelta(days=100),
            ),
        ]

        db.add_all(subscriptions)
        db.flush()

        payments = [
            Payment(
                customer_id=customers[0].id,
                subscription_id=subscriptions[0].id,
                amount=49.00,
                currency="USD",
                status="failed",
                failure_reason="insufficient_funds",
                due_date=now - timedelta(days=2),
            ),
            Payment(
                customer_id=customers[1].id,
                subscription_id=subscriptions[1].id,
                amount=99.00,
                currency="USD",
                status="failed",
                failure_reason="card_expired",
                due_date=now - timedelta(days=1),
            ),
            Payment(
                customer_id=customers[2].id,
                subscription_id=subscriptions[2].id,
                amount=49.00,
                currency="USD",
                status="paid",
                failure_reason=None,
                due_date=now - timedelta(days=5),
                paid_at=now - timedelta(days=5),
            ),
            Payment(
                customer_id=customers[3].id,
                subscription_id=subscriptions[3].id,
                amount=19.00,
                currency="USD",
                status="failed",
                failure_reason="card_declined",
                due_date=now - timedelta(days=3),
            ),
            Payment(
                customer_id=customers[4].id,
                subscription_id=subscriptions[4].id,
                amount=99.00,
                currency="USD",
                status="failed",
                failure_reason="bank_declined",
                due_date=now - timedelta(days=4),
            ),
            Payment(
                customer_id=customers[5].id,
                subscription_id=subscriptions[5].id,
                amount=49.00,
                currency="USD",
                status="paid",
                failure_reason=None,
                due_date=now - timedelta(days=8),
                paid_at=now - timedelta(days=8),
            ),
            Payment(
                customer_id=customers[6].id,
                subscription_id=subscriptions[6].id,
                amount=19.00,
                currency="USD",
                status="failed",
                failure_reason="network_error",
                due_date=now - timedelta(days=1),
            ),
            Payment(
                customer_id=customers[7].id,
                subscription_id=subscriptions[7].id,
                amount=49.00,
                currency="USD",
                status="paid",
                failure_reason=None,
                due_date=now - timedelta(days=10),
                paid_at=now - timedelta(days=10),
            ),
        ]

        db.add_all(payments)

        db.commit()

        print("Database seeded successfully!")
        print(f"Customers created: {len(customers)}")
        print(f"Subscriptions created: {len(subscriptions)}")
        print(f"Payments created: {len(payments)}")

    except Exception as error:
        db.rollback()
        print("Seed operation failed.")
        print(f"Error: {error}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()