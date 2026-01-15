import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    v = value.strip().lower()
    if v in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    # Modelo
    model_id: str
    hf_token: Optional[str]

    # Geração
    device: str  # auto|cpu|cuda
    use_quantization: bool
    max_new_tokens: int
    temperature: float
    top_p: float

    # API
    api_host: str
    api_port: int
    allowed_origins: List[str]

    # Rate limit
    rate_limit_per_minute: int

    # Logging
    log_level: str
    log_dir: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Carrega `.env` da raiz do projeto (medgemma-poc), independente do cwd.
    # Mantém override=False por segurança (variáveis já setadas no ambiente ganham).
    project_root = Path(__file__).resolve().parents[2]
    dotenv_path = project_root / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=False)

    model_id = os.getenv("MODEL_ID", "google/medgemma-4b-it")
    hf_token = os.getenv("HF_TOKEN") or None

    device = os.getenv("DEVICE", "auto")
    use_quantization = _parse_bool(os.getenv("USE_QUANTIZATION"), default=False)
    max_new_tokens = int(os.getenv("MAX_NEW_TOKENS", "512"))
    temperature = float(os.getenv("TEMPERATURE", "0.2"))
    top_p = float(os.getenv("TOP_P", "0.9"))

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", "8000"))
    allowed_origins = _split_csv(os.getenv("ALLOWED_ORIGINS"))

    rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_dir = os.getenv("LOG_DIR", "./data/logs")

    return Settings(
        model_id=model_id,
        hf_token=hf_token,
        device=device,
        use_quantization=use_quantization,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        api_host=api_host,
        api_port=api_port,
        allowed_origins=allowed_origins,
        rate_limit_per_minute=rate_limit_per_minute,
        log_level=log_level,
        log_dir=log_dir,
    )

