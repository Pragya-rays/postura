"""The rule registry. Rules register themselves at import time (see
scanner/rules/__init__.py); nothing here inspects the filesystem."""
from __future__ import annotations

from scanner.enums import ScanTier
from scanner.rules.base import Rule

_REGISTRY: dict[str, Rule] = {}


def register(rule: Rule) -> Rule:
    if rule.rule_id in _REGISTRY:
        raise ValueError(f"duplicate rule_id: {rule.rule_id!r}")
    _REGISTRY[rule.rule_id] = rule
    return rule


def all_rules(tier: ScanTier | None = None) -> list[Rule]:
    """All registered rules, or only those runnable at `tier` (VERIFIED
    unlocks everything; PUBLIC gets PUBLIC-tier rules only)."""
    rules = list(_REGISTRY.values())
    if tier is None or tier == ScanTier.VERIFIED:
        return rules
    return [r for r in rules if r.min_tier == ScanTier.PUBLIC]


def get_rule(rule_id: str) -> Rule | None:
    return _REGISTRY.get(rule_id)


def clear_registry() -> None:
    """Test-only: reset registry state between test modules that need a
    clean slate (e.g. testing duplicate-registration behavior)."""
    _REGISTRY.clear()
