"""Backend-only workflow enums (DB/API states). Domain-level Severity/Grade/
ScanTier live in scanner.enums since Judge produces them and scanner must
stay backend-independent — re-exported here so `app.models.enums` is the one
place backend code imports any enum from.
"""
from enum import Enum

from scanner.enums import Grade, Severity, ScanTier  # noqa: F401  (re-export)


class ScanStatus(str, Enum):
    QUEUED = "queued"
    COLLECTING = "collecting"
    JUDGING = "judging"
    EXPLAINING = "explaining"
    COMPLETE = "complete"
    FAILED = "failed"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class StageKey(str, Enum):
    COLLECT = "collect"
    JUDGE = "judge"
    EXPLAIN = "explain"
    PRESENT = "present"


class StageStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    ERROR = "error"


class SubscriptionStatus(str, Enum):
    """Mirrors the Stripe Subscription `status` values this app actually
    handles — kept in lockstep with webhook events in
    app/services/billing.py rather than the full set Stripe defines."""

    INCOMPLETE = "incomplete"
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class PlanTier(str, Enum):
    """Not stored anywhere — derived from SubscriptionStatus by
    app.services.billing.effective_tier, so there's nothing that can drift
    out of sync with Stripe."""

    FREE = "free"
    PRO = "pro"
