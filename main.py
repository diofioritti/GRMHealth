from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.dependencies import limiter
from src.api.routes.health_assistant import router as health_router
from src.core.config import get_settings
from src.core.logging import setup_logging


setup_logging()

settings = get_settings()

app = FastAPI(
    title="MedGemma POC API",
    version="0.1.0",
)

# Rate limiting (slowapi) - opcional (fallback se não estiver instalado)
try:
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi import _rate_limit_exceeded_handler

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
except Exception:
    # Sem rate limit. (Recomendado instalar `slowapi` em produção.)
    pass

# CORS
allowed_origins = settings.allowed_origins or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas API
app.include_router(health_router)


@app.get("/healthz")
def healthz():
    return {"ok": True}


# UI estática (HTML)
BASE_DIR = Path(__file__).resolve().parent
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")


@app.get("/")
def root():
    # Vai direto para o chat (se existir)
    return RedirectResponse(url="/ui/chat.html")

