# Postura — Frontend

Next.js 14 (App Router) frontend for Postura, built against the product spec
in the project brief. Design is a deliberate homage to
[pinecone.io](https://www.pinecone.io/): cream/parchment surface, near-black
ink, a signature chartreuse accent, an editorial serif for headlines paired
with a clean grotesk sans, pill-shaped nav/buttons, hairline borders instead
of heavy shadows, and a dark forest-green section for the pipeline story.

## Status

This is the frontend only, wired against a typed mock API layer
(`lib/api.ts`) so every screen is fully clickable today. Every function in
that file is a 1:1 stand-in for a real `backend/app/routers/*` endpoint —
swap the function body for a `fetch` call once FastAPI exists; no call site
changes. `lib/types.ts` mirrors the Pydantic schemas described in the spec
(`Finding`, `ScanReport`, `Domain`, …) so the swap is type-safe.

## Running it

```bash
npm install
npm run dev      # http://localhost:3000
npm run build    # production build (verified passing)
```

No environment variables are required to browse the mocked app. Once the
backend exists, set:

```
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Pages

| Route | What it is |
|---|---|
| `/` | Marketing landing page — hero, the Collect→Judge→Explain→Present pipeline, the 9 passive checks, a live Simple/Technical toggle demo, the MVP-vs-v2 roadmap |
| `/login`, `/register` | Auth screens. Copy notes argon2 hashing + httpOnly cookies; the real session cookie can only be set server-side once the FastAPI backend issues it |
| `/dashboard` | Domain list with grade rings + verification status, and scan history |
| `/dashboard/scans/new` | Pick an existing domain or add a new one; client-side SSRF-pattern pre-check (`lib/validate-target.ts`) mirrors the backend guard as a UX nicety only — the authoritative check is server-side |
| `/dashboard/scans/[id]` | Animated Collect→Judge→Explain→Present checklist, then the full report: grade, one-line AI summary, top-3 fixes, Simple/Technical toggle, severity chart, per-finding remediation |

## Design tokens

Defined in `tailwind.config.ts` under `cream` / `ink` / `lime` / `forest` /
`status`. The `status` colors (good/warning/serious/critical) are the fixed,
validated status palette from the project's dataviz skill — used for severity
badges and the severity-breakdown chart, always paired with an icon + text
label rather than color alone (two of the four are intentionally sub-3:1 on
the light surface; the icon+label pairing is the accessibility mitigation,
not a bug).

## Structure

```
app/                  routes (App Router)
components/marketing/ landing page sections
components/dashboard/ domain list, scan history, nav
components/report/    grade ring, severity badge/chart, finding cards, verify banner
components/ui/        button, card, badge, input, switch, progress
lib/                  types, mock API client, mock data, SSRF pre-check, utils
```

## Known follow-ups

- `next@14.2.15` is the latest stable 14.x release; `npm audit` flags several
  advisories fixed only in Next 16 (mostly Server Actions/Middleware DoS and
  cache-poisoning issues that don't apply to this mocked build). Re-audit
  before deploying against a real backend.
- Auth is currently a client-side redirect after a mocked `login`/`register`
  call — there is no real session yet and no route guarding. Add middleware-
  based cookie checks once the backend issues httpOnly JWT cookies.
