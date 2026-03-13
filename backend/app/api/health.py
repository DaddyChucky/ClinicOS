from __future__ import annotations

from fastapi import APIRouter

from app.agents.common import runtime_status, try_sdk_text
from app.config import get_settings
from app.models.schemas import HealthResponse, OpenAIHealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    settings = get_settings()
    return HealthResponse(status="ok", app=settings.app_name)


@router.get("/health/openai", response_model=OpenAIHealthResponse)
async def openai_health_check():
    status = runtime_status()
    detail: str | None = None
    test_call_success = False

    if status["live_mode_ready"]:
        output = await try_sdk_text(
            agent_name="Connectivity Health Check",
            instructions=(
                "You are a system connectivity check. "
                "Reply with exactly: ok"
            ),
            input_text="Return ok",
            tools=[],
        )
        test_call_success = bool(output and "ok" in output.lower())
        detail = (
            "ClinicOS AI is connected and ready for live responses."
            if test_call_success
            else "Live AI is configured, but the latest connectivity check did not complete successfully."
        )
    else:
        detail = "Live AI is unavailable in this environment, so ClinicOS falls back to its local guidance mode."

    runtime_mode = "live_ai" if test_call_success else "fallback"
    return OpenAIHealthResponse(
        status="ok",
        sdk_available=status["sdk_available"],
        api_key_loaded=status["api_key_loaded"],
        model=status["model"],
        live_mode_ready=status["live_mode_ready"],
        test_call_success=test_call_success,
        runtime_mode=runtime_mode,
        detail=detail,
    )
