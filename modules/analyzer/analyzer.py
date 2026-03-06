"""
LLM-based paper analysis: Skeleton Scan → Deep Dive → Cross-Check.

All public functions are async and accept pre-parsed sections (list[Section])
instead of raw markdown text — split_sections() is called once in pipeline.py
(Step 3) and the result is reused across all analysis steps.

    LLMFn = async (user_message: str, system_prompt: str | None) -> str

Usage:
    from modules.chunker.chunker import split_sections
    from modules.analyzer.analyzer import skeleton_scan, deep_dive, cross_check

    sections = split_sections(md_text)
    skeleton = await skeleton_scan(sections, llm)
    dive     = await deep_dive(sections, llm)
    check    = await cross_check(sections, llm)
"""
import asyncio
import logging
from typing import Callable, Awaitable, Optional

from modules.chunker.chunker import (
    Section,
    get_abstract,
    get_intro,
    get_conclusion,
    get_body_sections,
    annotate_paragraphs,
)
from modules.utils.utils import truncate

logger = logging.getLogger(__name__)

# Type alias
LLMFn = Callable[[str, Optional[str]], Awaitable[str]]

_MAX_SECTION_CHARS = 8000

# ── System prompts ────────────────────────────────────────────────────────────

_SKELETON_SYSTEM = """\
You are an expert academic paper analyst.
Given the Abstract and Introduction of a paper, produce a structured "paper map":

1. **Research Question / Hypothesis** — 1-2 sentences
2. **Proposed Method / Approach** — 1-2 sentences
3. **Key Contributions** — bullet list (3-5 items)
4. **Expected Section Structure** — brief note on what each section likely covers

Be concise, well-structured, and use Markdown formatting."""

_DEEP_DIVE_SYSTEM = """\
You are an expert academic paper analyst performing a section-level Deep Dive.
Each paragraph in the section is prefixed with [¶N] to help you pinpoint locations.
For the provided section, produce the following in Markdown:

## [Section Title] — Summary
[2-4 sentence summary of the key content and findings]

### Citation Map
- **[Section Title], ¶N**: [Key finding, data point, or argument — must reference the paragraph number]

Include 3-8 citation map entries per section. Every entry MUST cite a paragraph number (¶N).
Be precise and traceable."""

_CROSS_CHECK_SYSTEM = """\
You are an expert academic paper analyst. Perform a Cross-Check between the
Introduction and Conclusion of a paper:

1. **Hypothesis (from Introduction)** — state it clearly (verbatim or paraphrased)
2. **Conclusion Claim** — what does the conclusion actually assert?
3. **Verdict** — choose one: *Fully Proven* / *Partially Proven* / *Not Addressed*
   Then explain in 1-2 sentences why.

Be direct and evidence-based. Use Markdown formatting."""


# ── Public analysis functions ─────────────────────────────────────────────────

async def skeleton_scan(sections: list[Section], llm: LLMFn) -> str:
    """Step 4 — Analyse Abstract + Introduction to create a 'paper map'."""
    abstract = get_abstract(sections)
    intro = get_intro(sections)

    if not abstract and not intro:
        return "[Skeleton Scan: Abstract / Introduction 섹션을 찾을 수 없습니다.]"

    parts: list[str] = []
    if abstract:
        parts.append(f"## Abstract\n{abstract}")
    if intro:
        parts.append(f"## Introduction\n{intro}")

    logger.info("Skeleton Scan 시작")
    return await llm("\n\n".join(parts), _SKELETON_SYSTEM)


async def _analyse_section(sec: Section, llm: LLMFn) -> str:
    """단일 섹션에 대한 Deep Dive를 수행한다 (단락 번호 삽입 포함)."""
    annotated = annotate_paragraphs(sec)
    content = truncate(annotated, _MAX_SECTION_CHARS)
    user_msg = f"## {sec.title}\n\n{content}"
    return await llm(user_msg, _DEEP_DIVE_SYSTEM)


async def deep_dive(sections: list[Section], llm: LLMFn) -> str:
    """Step 5 — Per-section summary with Citation Map (¶N) for all body sections.

    섹션별 LLM 호출을 asyncio.gather()로 병렬 실행한다.
    """
    body = get_body_sections(sections)

    if not body:
        return "[Deep Dive: 분석할 본문 섹션을 찾을 수 없습니다.]"

    logger.info("Deep Dive 시작: %d 섹션 (병렬)", len(body))
    results: list[str] = await asyncio.gather(
        *[_analyse_section(sec, llm) for sec in body]
    )
    return "\n\n---\n\n".join(results)


async def cross_check(sections: list[Section], llm: LLMFn) -> str:
    """Step 6 — Verify that Intro hypothesis is addressed in Conclusion."""
    intro = get_intro(sections)
    conclusion = get_conclusion(sections)

    if not intro:
        return "[Cross-Check: Introduction 섹션을 찾을 수 없습니다.]"
    if not conclusion:
        return "[Cross-Check: Conclusion 섹션을 찾을 수 없습니다.]"

    user_msg = f"## Introduction\n{intro}\n\n## Conclusion\n{conclusion}"
    logger.info("Cross-Check 시작")
    return await llm(user_msg, _CROSS_CHECK_SYSTEM)
