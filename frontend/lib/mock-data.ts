import type { Domain, Finding, ScanReport, ScanStage, ScanSummary } from "./types";

export const MOCK_USER = {
  id: "usr_1",
  email: "pragya@postura.dev",
  createdAt: "2026-06-02T10:00:00Z",
};

export const MOCK_DOMAINS: Domain[] = [
  {
    id: "dom_1",
    hostname: "getbrightly.app",
    verificationStatus: "verified",
    verificationToken: "postura-verify-8f2a1c",
    addedAt: "2026-06-03T09:14:00Z",
    lastScan: {
      id: "scan_1",
      domainId: "dom_1",
      hostname: "getbrightly.app",
      status: "complete",
      tier: "verified",
      grade: "C",
      score: 68,
      startedAt: "2026-08-05T14:02:00Z",
      completedAt: "2026-08-05T14:03:21Z",
    },
  },
  {
    id: "dom_2",
    hostname: "northloop-consulting.com",
    verificationStatus: "unverified",
    verificationToken: "postura-verify-51de9b",
    addedAt: "2026-07-12T16:40:00Z",
    lastScan: {
      id: "scan_2",
      domainId: "dom_2",
      hostname: "northloop-consulting.com",
      status: "complete",
      tier: "public",
      grade: "B",
      score: 81,
      startedAt: "2026-08-06T08:11:00Z",
      completedAt: "2026-08-06T08:12:10Z",
    },
  },
  {
    id: "dom_3",
    hostname: "staging.pixelfoundry.io",
    verificationStatus: "pending",
    verificationToken: "postura-verify-c30f77",
    addedAt: "2026-08-01T11:02:00Z",
    lastScan: {
      id: "scan_3",
      domainId: "dom_3",
      hostname: "staging.pixelfoundry.io",
      status: "complete",
      tier: "public",
      grade: "F",
      score: 31,
      startedAt: "2026-08-07T07:40:00Z",
      completedAt: "2026-08-07T07:41:52Z",
    },
  },
];

export const MOCK_SCAN_HISTORY: ScanSummary[] = [
  MOCK_DOMAINS[0].lastScan!,
  {
    id: "scan_1b",
    domainId: "dom_1",
    hostname: "getbrightly.app",
    status: "complete",
    tier: "public",
    grade: "D",
    score: 54,
    startedAt: "2026-07-08T10:00:00Z",
    completedAt: "2026-07-08T10:01:40Z",
  },
  MOCK_DOMAINS[1].lastScan!,
  MOCK_DOMAINS[2].lastScan!,
];

export const SCAN_STAGES: ScanStage[] = [
  { key: "collect", label: "Collect", status: "done", detail: "27 signals gathered across 10 collectors" },
  { key: "judge", label: "Judge", status: "done", detail: "9 findings produced by deterministic rules" },
  { key: "explain", label: "Explain", status: "done", detail: "Plain-English + technical copy generated" },
  { key: "present", label: "Present", status: "done", detail: "Grade C · 68 / 100" },
];

const findings: Finding[] = [
  {
    id: "fnd_1",
    scanId: "scan_1",
    ruleId: "hdr.hsts.missing",
    title: "Strict-Transport-Security header is missing",
    category: "Security Headers",
    severity: "high",
    cvssVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N",
    cvssScore: 5.3,
    owaspCategory: "A05:2021 – Security Misconfiguration",
    evidence: { header: "strict-transport-security", present: false, checkedUrl: "https://getbrightly.app/" },
    simpleExplanation:
      "Your site doesn't tell browsers to always use HTTPS. That leaves a small window where a visitor on a shady Wi-Fi network could be silently downgraded to plain HTTP and have their traffic intercepted.",
    technicalExplanation:
      "No Strict-Transport-Security response header was observed on the root document. Without HSTS, user agents fall back to protocol-relative navigation and are vulnerable to SSL-stripping on the first request in a session, before any redirect to HTTPS can be enforced.",
    remediation: [
      "Add `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` to every response.",
      "Confirm HTTPS is enforced on all subdomains before adding `includeSubDomains`.",
      "Submit the domain to the HSTS preload list once you've run it in production for a few weeks.",
    ],
    fromCache: true,
    aiGenerated: true,
  },
  {
    id: "fnd_2",
    scanId: "scan_1",
    ruleId: "hdr.csp.missing",
    title: "No Content-Security-Policy configured",
    category: "Security Headers",
    severity: "high",
    cvssVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
    cvssScore: 6.1,
    owaspCategory: "A03:2021 – Injection",
    evidence: { header: "content-security-policy", present: false },
    simpleExplanation:
      "There's no rulebook telling the browser which scripts are allowed to run on your site. If an attacker ever manages to sneak in a snippet of JavaScript — through a comment field, a compromised ad, or a vulnerable plugin — nothing stops it from running.",
    technicalExplanation:
      "No CSP header or meta tag was detected. Absent a policy, the browser applies no restriction on script-src, so any injected markup executes with full page privileges, materially raising the impact of a stored or reflected XSS finding elsewhere.",
    remediation: [
      "Start with a report-only policy: `Content-Security-Policy-Report-Only: default-src 'self'`.",
      "Inventory third-party scripts (analytics, chat widgets) and allowlist their exact origins.",
      "Move to enforcing mode once a week of reports shows no unexpected blocks.",
    ],
    fromCache: true,
    aiGenerated: true,
  },
  {
    id: "fnd_3",
    scanId: "scan_1",
    ruleId: "cookie.session.flags",
    title: "Session cookie missing SameSite and Secure flags",
    category: "Cookies",
    severity: "medium",
    cvssVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
    cvssScore: 5.4,
    owaspCategory: "A05:2021 – Security Misconfiguration",
    evidence: { cookie: "session_id", secure: false, httpOnly: true, sameSite: "None" },
    simpleExplanation:
      "Your login cookie can be sent over an insecure connection and along with cross-site requests. In practice, this makes cross-site request forgery and network-snooping attacks easier than they need to be.",
    technicalExplanation:
      "`session_id` was observed with `HttpOnly` set but `Secure` unset and `SameSite=None`. Combined, this permits transmission over plaintext HTTP and inclusion in cross-origin requests, weakening CSRF defenses that assume same-site cookie scoping.",
    remediation: [
      "Set `Secure` on every cookie that carries session state.",
      "Change `SameSite` to `Lax` (or `Strict` if no cross-site flows are needed).",
      "Re-issue existing sessions after the change so old cookies expire.",
    ],
    fromCache: false,
    aiGenerated: true,
  },
  {
    id: "fnd_4",
    scanId: "scan_1",
    ruleId: "dns.dmarc.missing",
    title: "No DMARC record published",
    category: "Email Authentication",
    severity: "medium",
    cvssVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N",
    cvssScore: 4.3,
    owaspCategory: "A05:2021 – Security Misconfiguration",
    evidence: { record: "_dmarc.getbrightly.app", found: false, spf: true, dkim: true },
    simpleExplanation:
      "Anyone can send an email that looks like it's from your domain, and there's no policy telling mail providers what to do about it. That makes your brand an easy target for phishing that impersonates you.",
    technicalExplanation:
      "SPF and DKIM records exist, but no DMARC (`_dmarc` TXT) record was found. Without DMARC, receiving MTAs have no alignment policy to enforce, so SPF/DKIM failures are not acted on consistently across providers.",
    remediation: [
      "Publish `v=DMARC1; p=none; rua=mailto:dmarc-reports@getbrightly.app` first to gather data.",
      "Review aggregate reports for two weeks, then move policy to `p=quarantine`.",
      "Graduate to `p=reject` once legitimate senders are all aligned.",
    ],
    fromCache: true,
    aiGenerated: true,
  },
  {
    id: "fnd_5",
    scanId: "scan_1",
    ruleId: "tls.cert.expiry",
    title: "TLS certificate expires in 11 days",
    category: "SSL / TLS",
    severity: "medium",
    cvssVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L",
    cvssScore: 3.7,
    owaspCategory: "A02:2021 – Cryptographic Failures",
    evidence: { issuer: "Let's Encrypt", notAfter: "2026-08-18T00:00:00Z", protocol: "TLSv1.3" },
    simpleExplanation:
      "The certificate that proves your site is really your site runs out in under two weeks. When it expires, every visitor's browser will show a scary warning page instead of your site.",
    technicalExplanation:
      "Leaf certificate `notAfter` is within the 14-day warning threshold. TLS negotiation currently succeeds on TLSv1.3 with no chain issues; the only defect is time-to-expiry.",
    remediation: [
      "Confirm auto-renewal (certbot / ACME client) is actually running and not silently failing.",
      "Add an expiry monitor with at least a 21-day lead time.",
      "Renew manually now if automation can't be confirmed before the deadline.",
    ],
    fromCache: true,
    aiGenerated: true,
  },
  {
    id: "fnd_6",
    scanId: "scan_1",
    ruleId: "hdr.xfo.missing",
    title: "X-Frame-Options / frame-ancestors not set",
    category: "Security Headers",
    severity: "low",
    cvssVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N",
    cvssScore: 3.1,
    owaspCategory: "A05:2021 – Security Misconfiguration",
    evidence: { header: "x-frame-options", present: false },
    simpleExplanation:
      "Your pages can be loaded inside an invisible frame on someone else's site, which is the classic setup for tricking users into clicking things they didn't mean to (clickjacking).",
    technicalExplanation:
      "Neither `X-Frame-Options` nor a CSP `frame-ancestors` directive was present, leaving framing policy at the browser default (allow).",
    remediation: [
      "Add `X-Frame-Options: DENY` for legacy browser support.",
      "Add `frame-ancestors 'none'` to your CSP as the modern equivalent.",
    ],
    fromCache: true,
    aiGenerated: true,
  },
  {
    id: "fnd_7",
    scanId: "scan_1",
    ruleId: "fingerprint.tech.outdated",
    title: "Outdated jQuery version exposed in page source",
    category: "Technology Fingerprint",
    severity: "low",
    cvssVector: "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
    cvssScore: 3.4,
    owaspCategory: "A06:2021 – Vulnerable and Outdated Components",
    evidence: { library: "jquery", version: "1.12.4", source: "script src fingerprint" },
    simpleExplanation:
      "A JavaScript library on your site was last updated years ago and has known public vulnerabilities. It's low urgency on its own, but it's an easy target if combined with something else.",
    technicalExplanation:
      "Script tag fingerprinting matched jQuery 1.12.4, which predates several documented XSS-class fixes in later 1.x and 3.x releases. No exploit was attempted; presence alone is being flagged.",
    remediation: [
      "Upgrade to a current jQuery 3.x release or drop the dependency if unused.",
      "Re-run this check after upgrading to confirm the fingerprint clears.",
    ],
    fromCache: true,
    // Cached copy that was originally generated while Gemini was
    // unavailable — ai_engine.fallback's static text, not a live AI call.
    aiGenerated: false,
  },
  {
    id: "fnd_8",
    scanId: "scan_1",
    ruleId: "cors.wildcard.credentials",
    title: "CORS allows any origin alongside credentials",
    category: "CORS",
    severity: "critical",
    cvssVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
    cvssScore: 8.6,
    owaspCategory: "A05:2021 – Security Misconfiguration",
    evidence: { header: "access-control-allow-origin", value: "*", allowCredentials: true, endpoint: "/api/account" },
    simpleExplanation:
      "One of your API endpoints will hand over logged-in users' data to literally any website that asks, cookies and all. Any site a visitor happens to have open in another tab could quietly read their account data.",
    technicalExplanation:
      "`/api/account` returns `Access-Control-Allow-Origin: *` together with `Access-Control-Allow-Credentials: true`. Browsers reject this exact combination for credentialed requests in spec-compliant clients, but the reflected-origin variant of this misconfiguration (echoing the request Origin verbatim) is exploitable and was observed on this endpoint — treat as a live cross-origin data exposure.",
    remediation: [
      "Never combine a wildcard or reflected origin with `Allow-Credentials: true`.",
      "Maintain an explicit allowlist of trusted origins for any credentialed endpoint.",
      "Add a regression test that fails the build if a wildcard + credentials pair reappears.",
    ],
    fromCache: false,
    aiGenerated: true,
  },
  {
    id: "fnd_9",
    scanId: "scan_1",
    ruleId: "disclosure.directory.listing",
    title: "Directory listing enabled on /assets/backups/",
    category: "Information Disclosure",
    severity: "high",
    cvssVector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
    cvssScore: 7.5,
    owaspCategory: "A01:2021 – Broken Access Control",
    evidence: { path: "/assets/backups/", status: 200, filesListed: 14 },
    simpleExplanation:
      "A backups folder on your server is just... browsable, like an open filing cabinet. Anyone who finds the URL can see and download whatever's in there.",
    technicalExplanation:
      "Requesting `/assets/backups/` returned HTTP 200 with an autoindex-style listing of 14 files, including two `.sql.gz` archives, rather than a 403/404.",
    remediation: [
      "Disable autoindexing on the web server (`Options -Indexes` on Apache, `autoindex off;` on nginx).",
      "Move backup archives outside the public web root entirely.",
      "Audit whether the exposed archives were already accessed and rotate any credentials they contain.",
    ],
    fromCache: false,
    aiGenerated: true,
  },
];

export const MOCK_REPORT: ScanReport = {
  scan: MOCK_DOMAINS[0].lastScan!,
  stages: SCAN_STAGES,
  summary:
    "getbrightly.app has solid TLS fundamentals but is missing key browser-security headers and has one critical CORS misconfiguration exposing account data — fix that first.",
  findings,
  severityBreakdown: {
    critical: 1,
    high: 3,
    medium: 3,
    low: 2,
    info: 0,
  },
};

export function reportForGrade(): ScanReport {
  return MOCK_REPORT;
}
