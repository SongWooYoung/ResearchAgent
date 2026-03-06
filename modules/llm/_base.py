"""공통 타임아웃/에러 처리 래퍼."""
import asyncio
import logging
from typing import Callable

logger = logging.getLogger(__name__)


async def call_with_timeout(fn: Callable, timeout_sec: float, backend_name: str) -> str:
    """fn()을 스레드에서 실행하고 타임아웃/예외를 공통 처리한다."""
    try:
        return await asyncio.wait_for(asyncio.to_thread(fn), timeout=timeout_sec)
    except asyncio.TimeoutError:
        logger.warning("%s timed out after %.1f seconds", backend_name, timeout_sec)
        return f"{backend_name} LLM 응답이 너무 오래 걸립니다. 잠시 후 다시 시도해 주세요."
    except Exception:
        logger.exception("%s 호출 중 예외 발생", backend_name)
        return f"{backend_name} LLM 호출 중 알 수 없는 오류가 발생했습니다."
