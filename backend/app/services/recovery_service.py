from app.models.payment import Payment


class RecoveryService:
    """
    Intelligent recovery decision engine.

    Determines the best recovery strategy for a failed payment
    using payment information, failure reason, transaction amount,
    and previous recovery attempts.
    """

    MAX_RETRIES = 3

    STRATEGIES = {
        "insufficient_funds": {
            "action": "retry_payment",
            "base_priority": "medium",
            "message": (
                "Retry the payment after allowing time "
                "for the customer to replenish funds."
            ),
        },
        "card_expired": {
            "action": "update_payment_method",
            "base_priority": "high",
            "message": (
                "Ask the customer to update their expired "
                "payment method."
            ),
        },
        "card_declined": {
            "action": "retry_payment",
            "base_priority": "medium",
            "message": (
                "Retry the payment because the card decline "
                "may be temporary."
            ),
        },
        "bank_declined": {
            "action": "contact_customer",
            "base_priority": "high",
            "message": (
                "Contact the customer because the bank "
                "rejected the transaction."
            ),
        },
        "network_error": {
            "action": "retry_payment",
            "base_priority": "low",
            "message": (
                "Retry the payment because the failure "
                "appears to be network-related."
            ),
        },
    }

    @classmethod
    def calculate_recovery_score(
        cls,
        payment: Payment,
        attempt_count: int = 0,
    ) -> int:
        """
        Calculate an intelligent recovery score from 0 to 100.

        Higher scores indicate a stronger opportunity for recovery.
        """

        if payment.status != "failed":
            return 0

        score = 50

        # Failure reason factor.
        failure_scores = {
            "network_error": 25,
            "insufficient_funds": 15,
            "card_declined": 10,
            "card_expired": 5,
            "bank_declined": 0,
        }

        score += failure_scores.get(
            payment.failure_reason,
            -20,
        )

        # Payment amount factor.
        # Smaller payments are generally easier to recover automatically.
        amount = float(payment.amount)

        if amount <= 25:
            score += 10
        elif amount <= 100:
            score += 5
        elif amount <= 500:
            score += 0
        else:
            score -= 10

        # Previous attempt penalty.
        score -= attempt_count * 10

        # Keep score inside the 0-100 range.
        return max(0, min(100, score))

    @classmethod
    def get_priority_from_score(cls, score: int) -> str:
        """
        Convert recovery score into a priority level.
        """

        if score >= 75:
            return "high"

        if score >= 50:
            return "medium"

        return "low"

    @classmethod
    def determine_strategy(
        cls,
        payment: Payment,
        attempt_count: int = 0,
    ) -> dict:
        """
        Determine the best recovery strategy.

        The decision is based on:
        - Payment status
        - Failure reason
        - Payment amount
        - Previous recovery attempts
        """

        if payment.status != "failed":
            return {
                "action": "no_action",
                "priority": "none",
                "score": 0,
                "message": (
                    "No recovery action is required because "
                    "the payment was successful."
                ),
                "reason": (
                    "Payment status is not failed."
                ),
            }

        strategy = cls.STRATEGIES.get(
            payment.failure_reason
        )

        if not strategy:
            return {
                "action": "manual_review",
                "priority": "high",
                "score": 0,
                "message": (
                    "Unknown payment failure reason. "
                    "Manual review is required."
                ),
                "reason": (
                    "The failure reason is not recognized "
                    "by the recovery engine."
                ),
            }

        score = cls.calculate_recovery_score(
            payment,
            attempt_count,
        )

        priority = cls.get_priority_from_score(score)

        # Retry-based strategies should be escalated when
        # the retry limit has already been reached.
        if (
            strategy["action"] == "retry_payment"
            and attempt_count >= cls.MAX_RETRIES
        ):
            return {
                "action": "manual_review",
                "priority": "high",
                "score": score,
                "message": (
                    "Maximum recovery attempts reached. "
                    "Manual review is required."
                ),
                "reason": (
                    f"This payment already has {attempt_count} "
                    "previous recovery attempts."
                ),
            }

        reason_parts = [
            f"Failure reason: {payment.failure_reason.replace('_', ' ')}.",
            f"Payment amount: {payment.currency} {float(payment.amount):.2f}.",
            f"Previous recovery attempts: {attempt_count}.",
        ]

        if payment.failure_reason == "network_error":
            reason_parts.append(
                "Network failures are often temporary, "
                "making an automatic retry a strong option."
            )

        elif payment.failure_reason == "insufficient_funds":
            reason_parts.append(
                "The payment may succeed after the customer "
                "replenishes available funds."
            )

        elif payment.failure_reason == "card_expired":
            reason_parts.append(
                "The payment method must be updated before "
                "another payment can succeed."
            )

        elif payment.failure_reason == "card_declined":
            reason_parts.append(
                "A temporary card decline may be resolved "
                "through a later retry."
            )

        elif payment.failure_reason == "bank_declined":
            reason_parts.append(
                "Bank rejection requires customer intervention "
                "before another transaction is attempted."
            )

        if attempt_count > 0:
            reason_parts.append(
                "Previous recovery attempts reduce the "
                "confidence of another automatic action."
            )

        return {
            "action": strategy["action"],
            "priority": priority,
            "score": score,
            "message": strategy["message"],
            "reason": " ".join(reason_parts),
        }

    @classmethod
    def can_retry(cls, attempt_count: int) -> bool:
        """
        Determine whether another recovery attempt is allowed.
        """

        return attempt_count < cls.MAX_RETRIES

    @classmethod
    def execute_strategy(
        cls,
        attempt,
        attempt_count: int = 0,
    ) -> dict:
        """
        Execute the recovery strategy associated with
        a recovery attempt.

        The actual payment provider or communication service
        can be integrated later. For now, this simulates the
        recovery action while enforcing the retry limit.
        """

        strategy = attempt.strategy

        if strategy == "retry_payment":

            if not cls.can_retry(attempt_count):
                return {
                    "success": False,
                    "action": "escalate",
                    "message": (
                        "Maximum recovery attempts reached. "
                        "Manual review is required."
                    ),
                }

            return {
                "success": True,
                "action": "payment_retry_requested",
                "message": "Payment retry has been requested.",
            }

        if strategy == "update_payment_method":
            return {
                "success": True,
                "action": "payment_method_update_requested",
                "message": (
                    "Customer has been prompted to update "
                    "their payment method."
                ),
            }

        if strategy == "contact_customer":
            return {
                "success": True,
                "action": "customer_contact_requested",
                "message": "Customer contact has been requested.",
            }

        if strategy == "manual_review":
            return {
                "success": True,
                "action": "manual_review_requested",
                "message": (
                    "Payment has been flagged for manual review."
                ),
            }

        return {
            "success": False,
            "action": "unknown_strategy",
            "message": f"Unknown recovery strategy: {strategy}",
        }