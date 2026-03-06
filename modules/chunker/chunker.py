"""Section splitter for academic paper markdown.

Priority order of detection:
  1. Markdown headings  (## 1. Introduction)
  2. Bold headings      (**Abstract** / **1. Introduction**)
  3. Numbered sections  (1 Introduction / 2.1 Method)
  4. All-caps headings  (ABSTRACT / INTRODUCTION)
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Section:
    title: str
    content: str
    level: int  # 0=preamble, 1=top-level, 2=subsection, …


# (pattern, extractor) pairs — tried in priority order
_PATTERNS: list[tuple[re.Pattern, object]] = [
    # ## Abstract  /  ## 1. Introduction  /  ### 3.1 Method
    (
        re.compile(r"^(#{1,4})\s+(.+?)$", re.MULTILINE),
        lambda m: (len(m.group(1)), m.group(2).strip()),
    ),
    # **Abstract** / **1. Introduction** / **2.1 Method** (pymupdf4llm bold headings)
    (
        re.compile(
            r"^\*\*((?:\d+(?:\.\d+)*\.?\s+)?[A-Z][^\*\n]{0,80})\*\*$",
            re.MULTILINE,
        ),
        lambda m: (
            m.group(1).split()[0].rstrip(".").count(".") + 1
            if m.group(1)[0].isdigit()
            else 1,
            m.group(1).strip(),
        ),
    ),
    # 1 Introduction  /  2.1 Method  /  1. Introduction
    (
        re.compile(r"^(\d+(?:\.\d+)*)[.\s]+([A-Z][^\n]{1,80})$", re.MULTILINE),
        lambda m: (m.group(1).count(".") + 1, f"{m.group(1)} {m.group(2).strip()}"),
    ),
    # ABSTRACT  /  INTRODUCTION  (all-caps, 4-50 chars)
    (
        re.compile(r"^([A-Z][A-Z\s]{3,49}[A-Z])$", re.MULTILINE),
        lambda m: (1, m.group(1).strip()),
    ),
]


_KEY_SECTION_WORDS = {
    "abstract", "introduction", "intro", "related", "method", "approach",
    "experiment", "evaluation", "result", "conclusion", "discussion", "summary",
}


def split_sections(md_text: str) -> list[Section]:
    """Split markdown text into sections. Returns at least one Section.

    Picks the pattern whose sections have the most academic-keyword titles,
    so table/figure captions (e.g. '# Trainable Parameters (%)') don't win
    over real bold-heading section structure.
    """
    best: list[Section] | None = None
    best_score = -1

    for pattern, extractor in _PATTERNS:
        matches = list(pattern.finditer(md_text))
        if len(matches) < 2:
            continue
        sections = _build_sections(md_text, matches, extractor)
        score = sum(
            1 for s in sections
            if any(kw in s.title.lower() for kw in _KEY_SECTION_WORDS)
        )
        if score > best_score:
            best_score = score
            best = sections

    return best if best is not None else [Section(title="Full Text", content=md_text.strip(), level=1)]


def _build_sections(text: str, matches: list, extractor) -> list[Section]:
    sections: list[Section] = []
    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.append(Section(title="Preamble", content=preamble, level=0))
    for i, match in enumerate(matches):
        level, title = extractor(match)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append(Section(title=title, content=content, level=level))
    return sections


# ── Convenience accessors ────────────────────────────────────────────────────

def find_section(sections: list[Section], keywords: list[str]) -> Optional[Section]:
    """Return the first section whose title contains any keyword (case-insensitive)."""
    for sec in sections:
        for kw in keywords:
            if kw.lower() in sec.title.lower():
                return sec
    return None


def get_abstract(sections: list[Section]) -> Optional[str]:
    sec = find_section(sections, ["abstract"])
    return sec.content if sec else None


def get_intro(sections: list[Section]) -> Optional[str]:
    sec = find_section(sections, ["introduction", "intro"])
    return sec.content if sec else None


def get_conclusion(sections: list[Section]) -> Optional[str]:
    sec = find_section(sections, ["conclusion", "discussion", "summary"])
    return sec.content if sec else None


_SKIP_TITLES = {
    "abstract", "preamble", "references", "bibliography",
    "acknowledgment", "acknowledgement", "impact statement",
}

_STOP_KEYWORDS = [
    "appendix", "supplementary",
]

# Appendix-style section prefixes (A.1, B., C.2 …)
_APPENDIX_PREFIX = re.compile(r"^[A-Z]\d*\.")


def annotate_paragraphs(section: Section) -> str:
    """섹션 콘텐츠의 각 단락 앞에 번호를 붙여 반환한다.

    LLM이 Citation Map에서 정확한 단락 위치를 참조할 수 있도록 한다.

    출력 예:
        [¶1] Diffusion models have achieved remarkable results...
        [¶2] However, their computational cost remains prohibitive...
    """
    paragraphs = [p.strip() for p in section.content.split("\n\n") if p.strip()]
    numbered = [f"[¶{i + 1}] {p}" for i, p in enumerate(paragraphs)]
    return "\n\n".join(numbered)


def get_body_sections(
    sections: list[Section],
    min_content_len: int = 100,
    max_level: int = 2,
) -> list[Section]:
    """Return body sections filtered by level, content length, and deduplication.

    - Stops at appendix / supplementary sections (and discards everything after)
    - Skips abstract, preamble, references, acknowledgements
    - Skips stubs shorter than min_content_len
    - Skips level > max_level (sub-sub-sections and deeper)
    - Deduplicates by title to remove repeated page-header noise
    """
    seen_titles: set[str] = set()
    result: list[Section] = []

    for s in sections:
        title_lower = s.title.lower().strip()
        title_stripped = s.title.strip()

        # Stop at appendix / supplementary headings
        if any(kw in title_lower for kw in _STOP_KEYWORDS):
            break
        # Stop at appendix-labelled subsections (A.1, B., C.2 …)
        if _APPENDIX_PREFIX.match(title_stripped):
            break

        # Skip but continue for front/back-matter sections
        if any(kw in title_lower for kw in _SKIP_TITLES):
            continue

        if s.level < 1 or s.level > max_level:
            continue

        if len(s.content) < min_content_len:
            continue

        # Deduplicate by normalised title (catches repeated page headers)
        if title_lower in seen_titles:
            continue
        seen_titles.add(title_lower)

        result.append(s)

    return result
