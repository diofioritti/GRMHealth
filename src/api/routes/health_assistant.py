from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Deque, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.api.dependencies import limiter
from src.core.config import get_settings
from src.models.schemas import (
    HealthQuery,
    HealthResponse,
    LogsResponse,
    LogItem,
    MetricsResponse,
    StatusResponse,
)
from src.services.medgemma_service import (
    DISCLAIMER_PTBR,
    SYSTEM_PROMPT_EXPLAIN_PTBR,
    SYSTEM_PROMPT_GENERAL_PTBR,
    SYSTEM_PROMPT_TRIAGE_PTBR,
    MedGemmaService,
)


router = APIRouter(prefix="/api/v1/health", tags=["health"])


_GEN_LIMIT = f"{get_settings().rate_limit_per_minute}/minute"

_total_requests = 0
_by_endpoint: Dict[str, int] = defaultdict(int)
_processing_time_sum_ms = 0.0
_last_request_iso: Optional[str] = None

_logs: Deque[dict] = deque(maxlen=500)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mask_ip(ip: str) -> str:
    # máscara simples: mantém apenas prefixo
    if not ip:
        return "unknown"
    if ":" in ip:  # ipv6
        parts = ip.split(":")
        return ":".join(parts[:3] + ["xxxx", "xxxx"])
    parts = ip.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3] + ["xxx"])
    return ip


def _preview_message(msg: str, limit: int = 120) -> str:
    m = (msg or "").replace("\n", " ").replace("\r", " ").strip()
    if len(m) <= limit:
        return m
    return m[:limit].rstrip() + "..."


def _track(endpoint: str, processing_time_ms: float) -> None:
    global _total_requests, _processing_time_sum_ms, _last_request_iso
    _total_requests += 1
    _by_endpoint[endpoint] += 1
    _processing_time_sum_ms += max(0.0, processing_time_ms)
    _last_request_iso = _now_iso()


def _log_interaction(endpoint: str, client_ip: str, processing_time_ms: float, model_used: str, message: str) -> None:
    _logs.append(
        {
            "ts_iso": _now_iso(),
            "endpoint": endpoint,
            "client_ip": _mask_ip(client_ip),
            "processing_time_ms": float(processing_time_ms),
            "model_used": model_used,
            "message_preview": _preview_message(message),
        }
    )


def _service() -> MedGemmaService:
    return MedGemmaService.get_instance()


@router.post("/query", response_model=HealthResponse)
@limiter.limit(_GEN_LIMIT)
def query(payload: HealthQuery, request: Request) -> HealthResponse:
    endpoint = "/query"
    try:
        result = _service().generate_response(
            prompt=payload.message,
            system_prompt=SYSTEM_PROMPT_GENERAL_PTBR,
            context=payload.context,
        )
        _track(endpoint, result.processing_time_ms)
        _log_interaction(endpoint, request.client.host if request.client else "", result.processing_time_ms, result.model_used, payload.message)
        return HealthResponse(
            response=result.text,
            disclaimer=DISCLAIMER_PTBR,
            model_used=result.model_used,
            processing_time_ms=result.processing_time_ms,
        )
    except Exception as e:
        logger.exception("Erro no endpoint {}: {}", endpoint, str(e))
        raise HTTPException(
            status_code=503,
            detail="Modelo indisponível no momento. Verifique o status do modelo e tente novamente.",
        )


@router.post("/triage", response_model=HealthResponse)
@limiter.limit(_GEN_LIMIT)
def triage(payload: HealthQuery, request: Request) -> HealthResponse:
    endpoint = "/triage"
    try:
        result = _service().generate_response(
            prompt=payload.message,
            system_prompt=SYSTEM_PROMPT_TRIAGE_PTBR,
            context=payload.context,
        )
        _track(endpoint, result.processing_time_ms)
        _log_interaction(endpoint, request.client.host if request.client else "", result.processing_time_ms, result.model_used, payload.message)
        return HealthResponse(
            response=result.text,
            disclaimer=DISCLAIMER_PTBR,
            model_used=result.model_used,
            processing_time_ms=result.processing_time_ms,
        )
    except Exception as e:
        logger.exception("Erro no endpoint {}: {}", endpoint, str(e))
        raise HTTPException(status_code=503, detail="Modelo indisponível no momento. Tente novamente.")


@router.post("/explain", response_model=HealthResponse)
@limiter.limit(_GEN_LIMIT)
def explain(payload: HealthQuery, request: Request) -> HealthResponse:
    endpoint = "/explain"
    try:
        result = _service().generate_response(
            prompt=payload.message,
            system_prompt=SYSTEM_PROMPT_EXPLAIN_PTBR,
            context=payload.context,
        )
        _track(endpoint, result.processing_time_ms)
        _log_interaction(endpoint, request.client.host if request.client else "", result.processing_time_ms, result.model_used, payload.message)
        return HealthResponse(
            response=result.text,
            disclaimer=DISCLAIMER_PTBR,
            model_used=result.model_used,
            processing_time_ms=result.processing_time_ms,
        )
    except Exception as e:
        logger.exception("Erro no endpoint {}: {}", endpoint, str(e))
        raise HTTPException(status_code=503, detail="Modelo indisponível no momento. Tente novamente.")


@router.get("/status", response_model=StatusResponse)
@limiter.limit("120/minute")
def status(request: Request) -> StatusResponse:
    s = get_settings()
    svc = _service()
    return StatusResponse(
        model_loaded=svc.is_loaded(),
        model_id=s.model_id,
        device=svc.device(),
        use_quantization=s.use_quantization,
        max_new_tokens=s.max_new_tokens,
        temperature=s.temperature,
        top_p=s.top_p,
        uptime_s=svc.uptime_s(),
    )


@router.get("/metrics", response_model=MetricsResponse)
@limiter.limit("120/minute")
def metrics(request: Request) -> MetricsResponse:
    avg = (_processing_time_sum_ms / _total_requests) if _total_requests else 0.0
    return MetricsResponse(
        total_requests=_total_requests,
        by_endpoint=dict(_by_endpoint),
        avg_processing_time_ms=float(avg),
        last_request_iso=_last_request_iso,
    )


@router.get("/logs", response_model=LogsResponse)
@limiter.limit("60/minute")
def logs(request: Request, cursor: Optional[str] = None, limit: int = 50) -> LogsResponse:
    # cursor simples: índice inicial (string int)
    try:
        start_idx = int(cursor) if cursor else 0
    except ValueError:
        start_idx = 0

    items = list(_logs)
    # Paginação “para frente”
    end_idx = min(len(items), start_idx + max(1, min(limit, 200)))
    page = items[start_idx:end_idx]
    next_cursor = str(end_idx) if end_idx < len(items) else None

    return LogsResponse(
        items=[LogItem(**x) for x in page],
        next_cursor=next_cursor,
    )

