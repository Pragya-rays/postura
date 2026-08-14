"""Judge stage entrypoint: RawBundle -> list[EvaluatedFinding]. Purely
deterministic — no AI is imported or called anywhere in this module, by
design, not just by convention."""
from __future__ import annotations

import logging

from scanner.enums import ScanTier
from scanner.models import EvaluatedFinding, RawBundle
from scanner.rules import registry

logger = logging.getLogger(__name__)


def judge(bundle: RawBundle, tier: ScanTier) -> list[EvaluatedFinding]:
    findings: list[EvaluatedFinding] = []
    for rule in registry.all_rules(tier):
        try:
            evidence = rule.evaluate(bundle)
        except Exception:
            # A broken rule must never take the whole Judge stage down with
            # it — log and skip, same failure posture as a broken collector.
            logger.exception("rule %s raised while evaluating %s", rule.rule_id, bundle.hostname)
            continue
        if evidence is None:
            continue
        findings.append(
            EvaluatedFinding(
                rule_id=rule.rule_id,
                title=rule.title,
                category=rule.category,
                severity=rule.severity,
                cvss_vector=rule.cvss_vector,
                cvss_score=rule.cvss_score,
                owasp_category=rule.owasp_category,
                evidence=evidence,
                remediation=list(rule.remediation),
            )
        )
    return findings
