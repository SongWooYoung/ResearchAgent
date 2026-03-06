"""
Tool definitions for the Ollama function-calling agent.

TOOL_DEFINITIONS  — list of tool schemas to pass to ollama.chat(tools=...)
call_tool()       — sync dispatcher for simple (non-pipeline) tools
"""
import json
from modules.HTTP_request.HTTP_request import parse_and_validate_pdf_url, extract_https_url
from modules.pdf2md.pdf2md import extract_md_from_url

# ── Ollama tool schemas ───────────────────────────────────────────────────────

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "run_research_pipeline",
            "description": (
                "URL이 포함된 입력으로 논문 전체 분석 파이프라인을 실행합니다. "
                "(URL 검증 → PDF 변환 → Skeleton Scan → Deep Dive → Cross-Check) "
                "사용자가 논문 URL을 제공했을 때 이 도구를 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "논문 URL을 포함한 사용자 입력 원문",
                    }
                },
                "required": ["user_input"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_pdf_url",
            "description": "사용자 입력에서 PDF URL을 추출하고 접근 가능한지 검증합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "URL이 포함된 텍스트",
                    }
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_pdf_as_markdown",
            "description": "PDF URL에서 논문을 다운로드하고 Markdown으로 변환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "PDF 파일의 직접 URL",
                    }
                },
                "required": ["url"],
            },
        },
    },
]


def call_tool(name: str, args: dict | str) -> str:
    """Synchronous dispatcher for simple (non-pipeline) tools."""
    if isinstance(args, str):
        args = json.loads(args)

    if name == "validate_pdf_url":
        ok, result = parse_and_validate_pdf_url(args["text"])
        return result if ok else f"오류: {result}"

    if name == "fetch_pdf_as_markdown":
        return extract_md_from_url(args["url"])

    return f"알 수 없는 도구: {name}"
