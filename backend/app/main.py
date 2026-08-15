"""FastAPI app factory."""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_engine.fallback import check_fallback_coverage
from app.config import get_settings
from app.routers import auth as auth_router
from app.routers import billing as billing_router
from app.routers import domains as domains_router
from app.routers import scans as scans_router
from app.security.plan_limits import PlanLimitExceeded
from app.security.rate_limit import RateLimitExceeded
from app.security.ssrf import SSRFError
from scanner.rules import registry as _rules_registry  # noqa: F401 — import registers every rule

logger = logging.getLogger(__name__)
settings = get_settings()

# Startup self-check: every registered Judge rule must have fallback
# explanation copy, so a new rule can never ship without it and silently
# degrade to nothing if Gemini is ever unavailable. Runs at import time
# (module load = process startup), not inside a request.
check_fallback_coverage()

app = FastAPI(title="Postura API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,  # required: auth relies on httpOnly cookies, not bearer tokens
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(billing_router.router)
app.include_router(domains_router.router)
app.include_router(scans_router.router)


# --- Exception handlers ---
# AuthError (app/deps.py) needs no handler of its own — it subclasses
# HTTPException, which FastAPI already handles with its declared status
# code. These three are a safety net: every current call site already
# catches SSRFError/RateLimitExceeded locally (to attach an audit-log entry
# before converting to an HTTPException), so these only fire if some future
# code path forgets to — turning what would otherwise be an unhandled 500
# into the correct status code instead.


@app.exception_handler(SSRFError)
async def ssrf_error_handler(request: Request, exc: SSRFError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": str(exc)})


@app.exception_handler(PlanLimitExceeded)
async def plan_limit_handler(request: Request, exc: PlanLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=402, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Full traceback server-side only — never leak internals to the client.
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
