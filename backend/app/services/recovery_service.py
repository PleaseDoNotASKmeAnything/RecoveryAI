from app.models.payment import Payment


class RecoveryService:
    """
    Determines and executes the appropriate recovery strategy
    for a failed payment.
    """

    MAX_RETRIES = 3

    STRATEGIES = {
        "insufficient_funds": {
            "action": "retry_payment",
            "priority": "medium",
            "message": (
                "Retry the payment after allowing time "
                "for the customer to replenish funds."
            ),
        },
        "card_expired": {
            "action": "update_payment_method",
            "priority": "high",
            "message": (
                "Ask the customer to update their expired "
                "payment method."
            ),
        },
        "card_declined": {
            "action": "retry_payment",
            "priority": "medium",
            "message": (
                "Retry the payment because the card decline "
                "may be temporary."
            ),
        },
        "bank_declined": {
            "action": "contact_customer",
            "priority": "high",
            "message": (
                "Contact the customer because the bank "
                "rejected the transaction."
            ),
        },
        "network_error": {
            "action": "retry_payment",
            "priority": "low",
            "message": (
                "Retry the payment because the failure "
                "appears to be network-related."
            ),
        },
    }

    @classmethod
    def determine_strategy(cls, payment: Payment) -> dict:
        """
        Determine a recovery strategy for a payment.
        """

        if payment.status != "failed":
            return {
                "action": "no_action",
                "priority": "none",
                "message": (
                    "No recovery action is required because "
                    "the payment was successful."
                ),
            }

        strategy = cls.STRATEGIES.get(payment.failure_reason)

        if not strategy:
            return {
                "action": "manual_review",
                "priority": "high",
                "message": (
                    "Unknown payment failure reason. "
                    "Manual review is required."
                ),
            }

        return strategy

    @classmethod
    def can_retry(cls, attempt_count: int) -> bool:
        """
        Determine whether another recovery attempt is allowed.
        """

        return attempt_count < cls.MAX_RETRIES

    @classmethod
    def execute_strategy(cls, attempt, attempt_count: int = 0) -> dict:
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