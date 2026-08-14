"""Hardcoded fallback explanation copy, one entry per MVP rule_id. Used
whenever Gemini is unavailable, times out, or returns something that fails
validation — the scanner still produces a complete report either way. This
is not a lesser experience by accident: the copy here is written with the
same care as the prompt asks Gemini for, so a Gemini outage is invisible to
the end user.
"""
from __future__ import annotations

from ai_engine.schemas import ExplanationOutput

FALLBACK: dict[str, ExplanationOutput] = {
    "hdr.hsts.missing": ExplanationOutput(
        simple_explanation=(
            "Your site doesn't tell browsers to always use a secure connection. That leaves a brief "
            "window where a visitor on an untrusted network could be silently downgraded to an "
            "insecure connection and have their traffic intercepted."
        ),
        technical_explanation=(
            "No Strict-Transport-Security header was observed on the root document. Without HSTS, "
            "user agents can be downgraded to plain HTTP on the first request in a session, enabling "
            "SSL-stripping before any redirect to HTTPS takes effect."
        ),
    ),
    "hdr.csp.missing": ExplanationOutput(
        simple_explanation=(
            "There's no rulebook telling the browser which scripts are allowed to run on your site. "
            "If an attacker ever manages to sneak in a snippet of code, nothing stops it from running."
        ),
        technical_explanation=(
            "No Content-Security-Policy header or equivalent meta tag was detected. Absent a policy, "
            "the browser applies no restriction on script execution, materially raising the impact of "
            "any injection vulnerability elsewhere on the site."
        ),
    ),
    "hdr.xfo.missing": ExplanationOutput(
        simple_explanation=(
            "Your pages can be loaded inside an invisible frame on someone else's site, which is the "
            "classic setup for tricking visitors into clicking things they didn't mean to."
        ),
        technical_explanation=(
            "Neither X-Frame-Options nor a CSP frame-ancestors directive was present, leaving framing "
            "policy at the browser default of allowing it."
        ),
    ),
    "cookie.session.flags": ExplanationOutput(
        simple_explanation=(
            "A cookie that keeps visitors logged in can be sent over an insecure connection or along "
            "with requests from other sites. That makes it easier for an attacker to intercept "
            "sessions or forge requests on a visitor's behalf."
        ),
        technical_explanation=(
            "A session-like cookie was observed without both the Secure flag and a restrictive "
            "SameSite value, weakening protections against network interception and cross-site "
            "request forgery."
        ),
    ),
    "dns.dmarc.missing": ExplanationOutput(
        simple_explanation=(
            "Anyone can send an email that looks like it's from your domain, and there's no policy "
            "telling mail providers what to do about it. That makes your brand an easy target for "
            "phishing that impersonates you."
        ),
        technical_explanation=(
            "No DMARC (_dmarc TXT) record was found. Without DMARC, receiving mail servers have no "
            "alignment policy to enforce, so SPF/DKIM failures aren't consistently acted on across "
            "providers."
        ),
    ),
    "tls.cert.expiry": ExplanationOutput(
        simple_explanation=(
            "The certificate that proves your site is really your site is running out soon. When it "
            "expires, visitors' browsers will show a scary warning page instead of your site."
        ),
        technical_explanation=(
            "The leaf certificate's notAfter date falls within the warning threshold. TLS negotiation "
            "currently succeeds; the only defect flagged is time-to-expiry."
        ),
    ),
    "fingerprint.tech.outdated": ExplanationOutput(
        simple_explanation=(
            "A JavaScript library on your site was last updated years ago and has known public "
            "vulnerabilities. It's low urgency on its own, but it's an easy target if combined with "
            "something else."
        ),
        technical_explanation=(
            "Fingerprinting matched an outdated library version that predates several documented "
            "fixes in later releases. No exploit was attempted; presence alone is being flagged."
        ),
    ),
    "cors.wildcard.credentials": ExplanationOutput(
        simple_explanation=(
            "One of your endpoints will hand over logged-in users' data to nearly any website that "
            "asks, cookies included. Any site a visitor happens to have open in another tab could "
            "quietly read their account data."
        ),
        technical_explanation=(
            "A response was observed combining a wildcard or reflected-origin "
            "Access-Control-Allow-Origin with Access-Control-Allow-Credentials: true — a cross-origin "
            "data exposure for credentialed requests."
        ),
    ),
    "disclosure.directory.listing": ExplanationOutput(
        simple_explanation=(
            "A folder on your server is browsable like an open filing cabinet. Anyone who finds the "
            "URL can see and download whatever's inside."
        ),
        technical_explanation=(
            "A probed path returned an autoindex-style directory listing instead of a 403/404 "
            "response, exposing the contents of that directory to any visitor."
        ),
    ),
}

GENERIC_FALLBACK = ExplanationOutput(
    simple_explanation=(
        "We detected this issue but couldn't generate a plain-English explanation for it right now. "
        "It was still found by our automated checks and is worth reviewing."
    ),
    technical_explanation=(
        "Automated explanation generation was unavailable for this finding. Refer to the evidence "
        "captured alongside it for technical detail."
    ),
)


def check_fallback_coverage() -> None:
    """Startup self-check: every registered rule must have fallback copy —
    called from backend startup so a new rule can't ship without it and
    silently degrade to nothing if Gemini is ever unavailable."""
    from scanner.rules.registry import all_rules  # local import: avoids a hard import-time dependency on scanner.rules being populated

    missing = {r.rule_id for r in all_rules()} - set(FALLBACK)
    if missing:
        raise RuntimeError(f"Missing fallback explanation copy for rules: {sorted(missing)}")
