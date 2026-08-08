from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aukalabs"
    # Required — no default. The backend must not boot with a known secret.
    secret_key: str
    # Required — Resend API key for transactional emails.
    resend_api_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Attack-surface discovery knobs (Phase 3 — Orchestration + API).
    # The orchestrator applies these as bounded timeouts / defaults so a slow
    # external source cannot stall a scan. (crt.sh's own URL + timeout and the
    # TLS probe timeout are fixed in the discovery modules by design.)
    dns_timeout: float = 5.0
    http_timeout: float = 10.0
    # Default port/scheme for active fingerprinting of a discovered host.
    fingerprint_port: int = 443
    fingerprint_scheme: str = "https"

    # Optional-key LLM enrichment (Phase 4 — PR 3). ADR-005: OpenAI-compatible
    # client pointed at Groq. A missing key makes the client inert; the
    # enrichment service degrades to deterministic templates (spec R1).
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_timeout: float = 30.0

    model_config = {"env_file": ".env"}

    @property
    def llm_enabled(self) -> bool:
        """True when ``LLM_API_KEY`` is set — the client is only built then."""
        return bool(self.llm_api_key)


settings = Settings()
