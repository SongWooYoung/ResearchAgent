import os
import logging
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from modules.llm._base import call_with_timeout

load_dotenv()
logger = logging.getLogger(__name__)

_API_KEY = os.getenv("Gemini_API_KEY")
if not _API_KEY:
    raise RuntimeError("Gemini_API_KEY environment variable is not set.")

_client = genai.Client(api_key=_API_KEY)
_MODEL = os.getenv("Gemini_Model_Name", "gemini-2.5-flash")
_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT", "100"))


async def generate_reply(
    user_message: str,
    system_prompt: Optional[str] = None,
    timeout_sec: Optional[float] = None,
) -> str:
    if not user_message.strip():
        return "빈 메시지는 처리할 수 없습니다."

    timeout = timeout_sec if timeout_sec is not None else _TIMEOUT
    config = types.GenerateContentConfig(
        system_instruction=system_prompt if system_prompt else None,
    )

    def _call():
        logger.info("Calling Gemini model: %s", _MODEL)
        return _client.models.generate_content(
            model=_MODEL,
            contents=user_message,
            config=config,
        )

    result = await call_with_timeout(_call, timeout, "Gemini")
    if isinstance(result, str):
        return result  # 타임아웃/에러 메시지

    text = getattr(result, "text", "") or ""
    return text or "[Gemini LLM 응답이 비어 있습니다.]"
