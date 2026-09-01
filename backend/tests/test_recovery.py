from decimal import Decimal

from app.models.payment import Payment
from app.services.recovery_service import RecoveryService


def make_payment(
    status="failed",
    failure_reason="card_declined",
    amount=50,
    currency="USD",
):
    return Payment(
        status=status,
        failure_reason=failure_reason,
        amount=Decimal(str(amount)),
        currency=currency,
    )


def test_network_error_gets_retry_strategy():
    payment = make_payment(
        failure_reason="network_error",
        amount=19,
    )

    result = RecoveryService.determine_strategy(
        payment,
        attempt_count=0,
    )

    assert result["action"] == "retry_payment"
    assert result["score"] == 85
    assert result["priority"] == "high"


def test_card_expired_requires_payment_method_update():
    payment = make_payment(
        failure_reason="card_expired",
        amount=99,
    )

    result = RecoveryService.determine_strategy(
        payment,
        attempt_count=0,
    )

    assert result["action"] == "update_payment_method"
    assert result["score"] == 60
    assert result["priority"] == "medium"


def test_bank_declined_contacts_customer():
    payment = make_payment(
        failure_reason="bank_declined",
        amount=99,
    )

    result = RecoveryService.determine_strategy(
        payment,
        attempt_count=0,
    )

    assert result["action"] == "contact_customer"
    assert result["score"] == 55
    assert result["priority"] == "medium"


def test_retry_strategy_escalates_after_max_retries():
    payment = make_payment(
        failure_reason="card_declined",
        amount=19,
    )

    result = RecoveryService.determine_strategy(
        payment,
        attempt_count=3,
    )

    assert result["action"] == "manual_review"
    assert result["priority"] == "high"
    assert result["score"] == 40


def test_retry_is_allowed_below_limit():
    assert RecoveryService.can_retry(0) is True
    assert RecoveryService.can_retry(1) is True
    assert RecoveryService.can_retry(2) is True


def test_retry_is_blocked_at_limit():
    assert RecoveryService.can_retry(3) is False
    assert RecoveryService.can_retry(4) is False


def test_successful_payment_requires_no_action():
    payment = make_payment(
        status="successful",
        failure_reason="card_declined",
        amount=50,
    )

    result = RecoveryService.determine_strategy(
        payment,
        attempt_count=0,
    )

    assert result["action"] == "no_action"
    assert result["priority"] == "none"
    assert result["score"] == 0


def test_unknown_failure_reason_requires_manual_review():
    payment = make_payment(
        failure_reason="some_unknown_error",
        amount=50,
    )

    result = RecoveryService.determine_strategy(
        payment,
        attempt_count=0,
    )

    assert result["action"] == "manual_review"
    assert result["priority"] == "high"


def test_retry_execution_succeeds_below_limit():
    payment = make_payment(
        failure_reason="card_declined",
        amount=19,
    )

    strategy = RecoveryService.determine_strategy(
        payment,
        attempt_count=1,
    )

    class FakeAttempt:
        pass

    attempt = FakeAttempt()
    attempt.strategy = strategy["action"]

    result = RecoveryService.execute_strategy(
        attempt,
        attempt_count=1,
    )

    assert result["success"] is True
    assert result["action"] == "payment_retry_requested"


def test_retry_execution_escalates_at_limit():
    class FakeAttempt:
        pass

    attempt = FakeAttempt()
    attempt.strategy = "retry_payment"

    result = RecoveryService.execute_strategy(
        attempt,
        attempt_count=3,
    )

    assert result["success"] is False
    assert result["action"] == "escalate"


def test_update_payment_method_execution():
    class FakeAttempt:
        pass

    attempt = FakeAttempt()
    attempt.strategy = "update_payment_method"

    result = RecoveryService.execute_strategy(attempt)

    assert result["success"] is True
    assert result["action"] == "payment_method_update_requested"


def test_contact_customer_execution():
    class FakeAttempt:
        pass

    attempt = FakeAttempt()
    attempt.strategy = "contact_customer"

    result = RecoveryService.execute_strategy(attempt)

    assert result["success"] is True
    assert result["action"] == "customer_contact_requested"


def test_manual_review_execution():
    class FakeAttempt:
        pass

    attempt = FakeAttempt()
    attempt.strategy = "manual_review"

    result = RecoveryService.execute_strategy(attempt)

    assert result["success"] is True
    assert result["action"] == "manual_review_requested"