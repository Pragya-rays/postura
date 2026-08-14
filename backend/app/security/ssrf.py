"""Re-export shim. The real SSRF guard lives in scanner/security/ssrf.py —
it's the package that actually makes outbound requests to scan targets, and
must stay usable standalone via `python -m scanner` without a backend
dependency. This module exists at this exact path because
frontend/lib/validate-target.ts's comment names it as the authoritative
implementation; keeping the path stable avoids that comment going stale.
"""
from scanner.security.ssrf import (  # noqa: F401
    GuardedAsyncClient,
    ResolvedTarget,
    SSRFError,
    resolve_and_validate,
)
