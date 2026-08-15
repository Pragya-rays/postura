# Postura

Self-service website security scanner for people who own a website but
aren't security engineers. Enter a domain, get back a plain-English report
with a letter grade and copy-paste fixes — not a wall of CVEs.

**One-liner:** deterministic security detection, AI-written explanations,
and an ownership-verification gate so it can't be used as an attack tool.

## How it works

```
Collect  →  Judge  →  Explain  →  Present
(facts)     (rules)    (AI)       (UI)
```

- **Collect** (`scanner/scanner/collectors/`) — pure data gathering. No
  opinions. DNS, TLS cert, security headers, cookies, robots.txt/sitemap,
  WHOIS, tech fingerprint, CORS, directory listing — stored as raw JSON.
- **Judge** (`scanner/scanner/rules/`) — deterministic Python functions turn
  raw facts into `Finding`s (severity, CVSS, OWASP category). No AI, ever.
- **Explain** (`ai-engine/`) — the *only* place an LLM touches the system.
  Gemini writes plain-English + technical copy for a finding it's handed;
  it never decides whether something is a vulnerability, and every rule has
  hardcoded fallback copy so a Gemini outage never produces a degraded
  report.
- **Present** (`frontend/`) — grade, scoring, Simple/Technical toggle.

This separation is the single most important architectural decision in the
project: the AI can never invent a vulnerability that doesn't exist, and it
never sees the target site directly — only structured findings — which
also closes the prompt-injection door.

Every scan starts at a **Public** tier (safe, no-permission-required checks
only). Verifying domain ownership (DNS TXT record or a `.well-known` file)
unlocks a **Verified** tier with checks that assume you actually control
the target (CORS misconfiguration, directory listing).

## Quickstart (Docker)

Requires Docker + Docker Compose. This is the fastest way to run the whole
stack — Postgres, FastAPI, and Next.js — with zero local Python/Node setup.

```bash
cd docker
docker compose up
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (interactive API docs at `/docs`)

That's it — no `.env` file is required to get running. Every backend
setting has a working default for this exact network baked into
`backend/app/config.py`; the only thing docker-compose overrides is
`DATABASE_URL` (pointing at the `postgres` service instead of localhost).
Explanations fall back to hardcoded copy if `GEMINI_API_KEY` isn't set, so
the app is fully usable without any secrets configured.

**Optional overrides** — copy `docker/.env.example` to `docker/.env`:
- `GEMINI_API_KEY` — enables real AI-written explanations instead of the
  fallback copy
- `FRONTEND_PORT` — if 3000 is already taken on your host (CORS is
  configured to track this automatically)
- `JWT_SECRET` — only worth setting outside throwaway local dev

## Manual setup (without Docker)

Useful for active backend/scanner development, where a rebuild-on-every-edit
Docker loop is slower than you want.

**Prerequisites:** Python 3.12+, Node 20+, a running Postgres 16 instance.

```bash
# Postgres (or point DATABASE_URL at any Postgres 16 instance you already have)
docker run -d --name postura-postgres -e POSTGRES_USER=postura \
  -e POSTGRES_PASSWORD=postura -e POSTGRES_DB=postura -p 5432:5432 postgres:16-alpine

# Python packages — order matters: scanner has no local deps, ai-engine
# depends on scanner, backend depends on both.
cd scanner && pip install -e .[dev] && cd ..
cd ai-engine && pip install -e .[dev] && cd ..
cd backend && pip install -e .[dev]

cp .env.example .env   # then edit DATABASE_URL if not using the container above
alembic upgrade head
uvicorn app.main:app --reload   # http://localhost:8000
```

```bash
# in a second terminal
cd frontend
npm install
cp .env.local.example .env.local
npm run dev   # http://localhost:3000
```

The standalone scanner package also runs on its own, no backend or database
needed:

```bash
cd scanner
python -m scanner example.com
```

## Testing

No live network calls happen anywhere in the suites (SSRF/DNS/HTTP calls
are fixture-based or monkeypatched) — the scanner and ai-engine suites need
nothing but Python; the backend suite needs a disposable Postgres (tables
are created fresh per session and dropped after).

```bash
cd scanner    && pytest -q     # 64 tests — collectors, rules, scoring
cd ai-engine  && pytest -q     # 18 tests — schemas, cache, fallback coverage
cd backend    && pytest -q     # 20 tests — needs DATABASE_URL reachable
```

## Repo structure

```
postura/
  frontend/     Next.js 14 (App Router) — dashboard, scan flow, report UI
  backend/      FastAPI app — routers, auth, models, Alembic migrations
  scanner/      Standalone package: collectors + Judge rules engine
                (no web-framework dependency; runnable on its own)
  ai-engine/    Explain stage — Gemini client, prompt templates, schema
                validation, fallback copy, explanation cache interface
  docker/       docker-compose.yml + Dockerfiles
  docs/         (reserved for architecture diagrams / screenshots)
```

## Data model

| Table | Purpose |
|---|---|
| `users` | email, password hash (argon2), created_at |
| `domains` | owning user, hostname, verification status/token |
| `scans` | owning domain, status, tier, grade, score, live `stages` progress |
| `scan_raw` | one row per collector per scan — raw JSONB payload, permanent audit trail, never deleted |
| `findings` | one row per Judge output — severity/CVSS/OWASP, evidence, and a **denormalized copy** of the explanation text at scan time, so a historical report never silently changes if the shared cache entry is later regenerated |
| `explanations` | shared AI-explanation cache keyed by `(rule_id, context_hash)` — not by user or scan, so identical findings across every user reuse one Gemini call |
| `audit_log` | who did what, when, from which IP — scan starts, rate-limit hits, SSRF blocks, login attempts |

## Security principles

1. **SSRF guard on every outbound request** — hostnames are resolved
   server-side and checked against RFC1918/loopback/link-local/metadata-
   endpoint ranges, re-checked after every redirect. Verified: submitting
   `169.254.169.254` or `localhost` as a domain is rejected with a 422
   before any row is created or any network call is made.
2. **Judge is deterministic; only Explain touches an LLM.** The model never
   sees the target site directly — only structured findings — which also
   closes the prompt-injection door.
3. **Ownership verification gates deeper checks.** The Public tier only
   ever touches data that's already public.
4. **Auth tokens live in httpOnly cookies**, never localStorage.
5. **Remediation steps are static, rule-authored content — never AI
   output.** Exact header/syntax instructions are exactly what an LLM
   could plausibly hallucinate wrong, which would be actively harmful
   advice from a security product.
6. **Rate limiting + audit log** on every scan request (per-user and
   per-target, DB-backed — see `backend/app/security/rate_limit.py` for
   its documented multi-worker limitation).

## Status

The full pipeline runs end-to-end and has been exercised against a live
target through the Docker stack: register → add domain → scan → grade,
plain-English summary, and ranked findings, each with both a Simple and a
Technical explanation.

**Built:** auth, dashboard, all 10 passive collectors, 13 Judge rules,
AI explanations with caching and fallback, domain verification, SSRF
guard, rate limiting, audit log, Docker Compose stack.

**Known gaps / not yet judged:** `robots.txt`/`sitemap.xml` presence and
WHOIS are collected but currently informational only — no Judge rule
turns their absence into a finding yet.

## Roadmap (explicitly out of scope for the MVP)

- **Active scanning** — Nmap, OWASP ZAP, Nuclei (needs a VPS, real legal
  exposure, gated behind verification + explicit confirmation)
- **SSL Labs API** deep check (rate-limited, low value early)
- **Digital Footprint / OSINT module** — CT-log subdomain enumeration,
  dangling-CNAME takeover check, public GitHub secret scanning, HIBP
  domain breach check
- **Redis + Arq job queue and SSE progress streaming** — FastAPI
  `BackgroundTasks` + polling is enough for MVP scan volumes
- **Monetization** — freemium subscription (Stripe Checkout + Billing
  Portal + webhooks), gated by usage volume and report depth, never by
  safety features or verification
- GitHub Actions CI, refresh-token rotation, rescan diffing, demo video
