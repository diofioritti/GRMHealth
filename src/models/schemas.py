from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class HealthQuery(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    context: Optional[str] = Field(default=None, max_length=8000)
    language: str = Field(default="pt-BR", min_length=2, max_length=16)


class HealthResponse(BaseModel):
    response: str
    disclaimer: str
    model_used: str
    processing_time_ms: float


class StatusResponse(BaseModel):
    model_loaded: bool
    model_id: str
    device: str
    use_quantization: bool
    max_new_tokens: int
    temperature: float
    top_p: float
    uptime_s: float


class MetricsResponse(BaseModel):
    total_requests: int
    by_endpoint: Dict[str, int]
    avg_processing_time_ms: float
    last_request_iso: Optional[str]


class LogItem(BaseModel):
    ts_iso: str
    endpoint: str
    client_ip: str
    processing_time_ms: float
    model_used: str
    message_preview: str


class LogsResponse(BaseModel):
    items: List[LogItem]
    next_cursor: Optional[str]

