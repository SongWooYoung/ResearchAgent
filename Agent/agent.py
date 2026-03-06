"""
Research Agent orchestrator.

Routing logic:
  • URL detected in message → run_pipeline() directly (fast path)
  • No URL → Ollama tool-calling loop (LLM decides what to do)
      - LLM calls run_research_pipeline → async pipeline
      - LLM calls validate_pdf_url / fetch_pdf_as_markdown → sync wrappers
      - LLM answers directly → return content

Usage:
    result = await run_agent("https://arxiv.org/pdf/2410.09016", backend="ollama")
    result = await run_agent("Diffusion model이 뭔가요?", backend="gemini")
"""
import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from ollama import chat as ollama_chat

from modules.HTTP_request.HTTP_request import extract_https_url
from modules.llm import get_llm
from Agent.pipeline import run_pipeline
from Agent.tools import TOOL_DEFINITIONS, call_tool

load_dotenv()
logger = logging.getLogger(__name__)

AGENT_MODEL = os.getenv("AGENT_MODEL", "gemma3:12b")
_MAX_TOOL_TURNS = 6

_AGENT_SYSTEM = """\
You are ResearchAgent, an expert AI assistant specialising in academic paper analysis.

Available tools:
- run_research_pipeline : analyse a paper from a URL (full pipeline)
- validate_pdf_url      : check if a URL points to a valid PDF
- fetch_pdf_as_markdown : download and convert a PDF to Markdown

Guidelines:
- If the user provides a URL (arXiv, PDF link, etc.), call run_research_pipeline.
- If the user asks a general academic question, answer directly without tools.
- Always reply in the same language as the user."""


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_agent(user_message: str, backend: str = "ollama") -> str:
    """
    Process a user message and return a response string.

    Fast path: URL detected → run full pipeline immediately.
    Slow path: no URL → Ollama tool-calling loop (최대 _MAX_TOOL_TURNS회).
    """
    # Fast path — URL present, skip tool-calling overhead
    if extract_https_url(user_message):
        logger.info("[Agent] URL 감지 → 파이프라인 직접 실행")
        llm = get_llm(backend)
        return await run_pipeline(user_message, llm)

    # Slow path — general query, let the LLM decide via tool-calling loop
    logger.info("[Agent] 일반 질문 → Ollama tool-calling 루프 (최대 %d턴)", _MAX_TOOL_TURNS)
    messages = [
        {"role": "system", "content": _AGENT_SYSTEM},
        {"role": "user", "content": user_message},
    ]

    for turn in range(_MAX_TOOL_TURNS):
        response = await asyncio.to_thread(
            ollama_chat,
            model=AGENT_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )
        msg = response.message

        # LLM이 tool call 없이 직접 답변 → 루프 종료
        if not msg.tool_calls:
            logger.info("[Agent] 직접 답변 (턴 %d)", turn + 1)
            return msg.content or "[응답 없음]"

        # tool call 결과를 messages에 추가
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": msg.tool_calls,
        })

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = tc.function.arguments

            logger.info("[Agent] 턴 %d — tool call: %s", turn + 1, fn_name)

            if fn_name == "run_research_pipeline":
                llm = get_llm(backend)
                tool_result = await run_pipeline(
                    fn_args.get("user_input", user_message), llm
                )
            else:
                tool_result = await asyncio.to_thread(call_tool, fn_name, fn_args)

            messages.append({"role": "tool", "content": tool_result})

    logger.warning("[Agent] 최대 반복 횟수(%d) 초과", _MAX_TOOL_TURNS)
    return "[최대 반복 횟수를 초과했습니다. 분석을 완성하지 못했습니다.]"
