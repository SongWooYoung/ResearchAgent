import os
import logging
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from modules.llm._base import call_with_timeout

load_dotenv()
logger = logging.getLogger(__name__)

_API_KEY = os.getenv("OpenAI_API_KEY")
if not _API_KEY:
    raise RuntimeError("OpenAI_API_KEY environment variable is not set.")

_client = OpenAI(api_key=_API_KEY)
_MODEL = os.getenv("OpenAI_Model_Name", "gpt-4o-mini")
_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "100"))


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
        logger.info("Calling OpenAI model: %s", _MODEL)
        return _client.chat.completions.create(
            model=_MODEL,
            messages=messages,
        )

    result = await call_with_timeout(_call, timeout, "OpenAI")
    if isinstance(result, str):
        return result  # 타임아웃/에러 메시지

    try:
        text = result.choices[0].message.content or ""
    except Exception:
        logger.exception("OpenAI 응답 파싱 중 예외 발생")
        return "OpenAI LLM 응답을 이해하지 못했습니다."

    return text or "[OpenAI LLM 응답이 비어 있습니다.]"
