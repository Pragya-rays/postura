"""Domain-level enums shared by the scanner (Collect/Judge) and, transitively,
by the backend (which stores/serves these values). Kept here — not in
backend/ — because Judge (which produces Severity/Grade) lives in this
framework-free package and must not depend on the backend.
"""
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Ordered worst-to-best; used for sorting findings and for zero-filling severityBreakdown.
SEVERITY_ORDER: list[Severity] = [
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
    Severity.INFO,
]


class Grade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class ScanTier(str, Enum):
    PUBLIC = "public"
    VERIFIED = "verified"
