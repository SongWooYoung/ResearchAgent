import os
import logging
from typing import Optional

from dotenv import load_dotenv
from ollama import chat as ollama_chat

from modules.llm._base import call_with_timeout

load_dotenv()
logger = logging.getLogger(__name__)

_MODEL = os.getenv("OLLAMA_MODEL_NAME", "gemma3:12b")
# Ollama는 단일 프로세스라 섹션이 많을수록 대기 시간이 누적된다.
# OLLAMA_TIMEOUT 환경변수로 조정 가능 (기본 300초).
_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))


async def generate_reply(
    user_message: str,
    system_prompt: Optional[str] = None,
    timeout_sec: Optional[float] = None,
) -> str:
    if not user_message.strip():
        return "빈 메시지는 처리할 수 없습니다."

    timeout = timeout_sec if timeout_sec is not None else _TIMEOUT

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    def _call():
        logger.info("Calling Ollama model: %s", _MODEL)
        return ollama_chat(
            model=_MODEL,
            messages=messages,
            options={"num_ctx": 131072},
        )

    result = await call_with_timeout(_call, timeout, "Ollama")
    if isinstance(result, str):
        return result  # 타임아웃/에러 메시지

    try:
        text = result.message.content or ""
    except Exception:
        logger.exception("Ollama 응답 파싱 중 예외 발생")
        return "Ollama LLM 응답을 이해하지 못했습니다."

    return text or "[Ollama LLM 응답이 비어 있습니다.]"
