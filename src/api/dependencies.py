from src.core.config import get_settings


try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    _settings = get_settings()

    # Limiter global (default por IP). Endpoints podem sobrescrever via decorator.
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{_settings.rate_limit_per_minute}/minute"],
    )
except Exception:  # pragma: no cover
    # Fallback: permite subir a API mesmo sem slowapi instalado.
    class _NoopLimiter:
        def limit(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

    limiter = _NoopLimiter()

