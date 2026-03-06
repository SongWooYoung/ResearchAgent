"""LLM 백엔드 팩토리.

Usage:
    from modules.llm import get_llm, LLMFn
    llm = get_llm("ollama")   # or "gemini", "openai"
    result = await llm("질문", "시스템 프롬프트")
"""
from typing import Callable, Awaitable, Optional

LLMFn = Callable[[str, Optional[str]], Awaitable[str]]


def get_llm(backend: str) -> LLMFn:
    """백엔드 이름으로 generate_reply 함수를 반환한다."""
    if backend == "gemini":
        from modules.llm.gemini import generate_reply
        return generate_reply
    if backend == "openai":
        from modules.llm.openai import generate_reply
        return generate_reply
    from modules.llm.ollama import generate_reply
    return generate_reply
