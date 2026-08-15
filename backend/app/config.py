"""Central app configuration. Everything reads from environment variables
(see backend/.env.example) via pydantic-settings — nothing here is hardcoded
except safe, non-secret defaults for local dev.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postura:postura@localhost:5432/postura"

    # --- Auth ---
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    cookie_name: str = "postura_session"
    cookie_secure: bool = False  # True in prod (HTTPS-only); False for local docker compose over http
    cookie_domain: str | None = None

    # --- AI ---
    gemini_api_key: str = ""
    # A rolling alias, not a pinned version — Google retires dated model
    # names (e.g. gemini-2.5-flash returned 404 "no longer available to new
    # users" for this project's key during testing); "latest" tracks
    # whatever's current instead of going stale.
    gemini_model: str = "gemini-flash-latest"
    gemini_timeout_seconds: float = 8.0

    # --- Scanner / SSRF ---
    # Optional allowlist of hostnames that bypass the private-IP SSRF block, for local testing only
    # (e.g. "localhost,127.0.0.1" if you deliberately want to scan a local fixture server).
    # NEVER set this in production.
    allowed_scan_targets: str = ""
    scan_http_timeout_seconds: float = 8.0
    scan_pipeline_timeout_seconds: float = 90.0

    # --- Rate limiting ---
    rate_limit_scans_per_user_per_window: int = 10
    rate_limit_scans_per_target_per_window: int = 5
    rate_limit_window_minutes: int = 10

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    # --- Billing (Stripe) ---
    # Empty by default: Checkout/Portal/webhook routes fail closed (clear
    # error, not a silent no-op) until these are actually configured.
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro: str = ""
    # Where Checkout/Portal send the browser back to (success/cancel/return
    # URLs) — the frontend origin, not the API's.
    frontend_url: str = "http://localhost:3000"
    free_tier_domain_limit: int = 1
    free_tier_scans_per_month: int = 5

    @property
    def allowed_scan_targets_list(self) -> list[str]:
        return [t.strip().lower() for t in self.allowed_scan_targets.split(",") if t.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
