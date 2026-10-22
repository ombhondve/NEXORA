"""
Telemetry, performance metrics, and instrumentation helpers.
"""

import time
from typing import Callable, Any
from functools import wraps
from recursive_osint.core.logging import get_logger

logger = get_logger("telemetry")


def timed_execution(name: str):
    """Decorator to measure and log execution duration of critical functions."""
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000.0
                logger.debug("Execution [%s] took %.2f ms", name, duration_ms)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000.0
                logger.debug("Execution [%s] took %.2f ms", name, duration_ms)

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
