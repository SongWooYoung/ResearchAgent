"""
Full 6-step Research Agent pipeline.

Step 1  — Extract & validate URL from free text (PDF or HTML)
Step 2  — Download and convert to Markdown
Step 3  — Section splitting (regex-based, done once and shared across Steps 4-6)
Step 4  — Skeleton Scan  : paper map from Abstract + Intro
Step 5  — Deep Dive      : per-section summary with Citation Map (¶N)
Step 6  — Cross-Check    : verify Intro hypothesis vs Conclusion

Returns a formatted Markdown report string.
"""
import asyncio
import logging
from typing import Callable, Awaitable, Optional

from modules.HTTP_request.HTTP_request import parse_and_validate_url
from modules.pdf2md.pdf2md import extract_md_from_url
from modules.html2md.html2md import extract_md_from_html
from modules.chunker.chunker import split_sections
from modules.analyzer.analyzer import skeleton_scan, deep_dive, cross_check

logger = logging.getLogger(__name__)

LLMFn = Callable[[str, Optional[str]], Awaitable[str]]


async def run_pipeline(user_input: str, llm: LLMFn) -> str:
    """Execute the complete research pipeline. Returns a Markdown report."""

    # ── Step 1: URL extraction & validation ───────────────────────────────────
    logger.info("[Pipeline] Step 1 — URL 파싱 및 검증")
    ok, url, content_type = await asyncio.to_thread(parse_and_validate_url, user_input)
    if not ok:
        return f"❌ URL 검증 실패: {url}"
    logger.info("[Pipeline] URL 확인: %s (type: %s)", url, content_type)

    # ── Step 2: URL → Markdown ────────────────────────────────────────────────
    logger.info("[Pipeline] Step 2 — 다운로드 및 Markdown 변환 (type: %s)", content_type)
    if content_type == "html":
        md_text = await asyncio.to_thread(extract_md_from_html, url)
    else:
        md_text = await asyncio.to_thread(extract_md_from_url, url)

    if md_text.startswith("변환 중 오류 발생"):
        return f"❌ 변환 실패: {md_text}"
    logger.info("[Pipeline] Markdown 변환 완료 (%d chars)", len(md_text))

    # ── Step 3: Section splitting (1회만 수행, Steps 4-6에서 재사용) ──────────
    logger.info("[Pipeline] Step 3 — 정규 표현식 챕터 분리")
    sections = split_sections(md_text)
    logger.info("[Pipeline] 섹션 수: %d", len(sections))

    # ── Step 4: Skeleton Scan ─────────────────────────────────────────────────
    logger.info("[Pipeline] Step 4 — Skeleton Scan")
    skeleton = await skeleton_scan(sections, llm)

    # ── Step 5: Deep Dive (병렬 처리) ─────────────────────────────────────────
    logger.info("[Pipeline] Step 5 — Deep Dive")
    dive = await deep_dive(sections, llm)

    # ── Step 6: Cross-Check ───────────────────────────────────────────────────
    logger.info("[Pipeline] Step 6 — Cross-Check")
    check = await cross_check(sections, llm)

    # ── Assemble report ───────────────────────────────────────────────────────
    report = (
        f"# 📄 논문 분석 리포트\n\n"
        f"**URL:** {url}\n\n"
        f"---\n\n"
        f"## 🗺️ Skeleton Scan (논문 지도)\n\n{skeleton}\n\n"
        f"---\n\n"
        f"## 🔬 Deep Dive (섹션별 분석)\n\n{dive}\n\n"
        f"---\n\n"
        f"## ✅ Cross-Check (가설 검증)\n\n{check}"
    )
    logger.info("[Pipeline] 분석 완료")
    return report
