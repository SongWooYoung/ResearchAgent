# ResearchAgent 리팩토링 계획

> 기준일: 2026-03-06
> 목적: workflow.md 명세와 실제 구현의 불일치 해소 + 구조적 결함 개선

---

## 0. 문제 전체 목록 (우선순위 순)

| # | 분류 | 파일 | 심각도 |
|---|------|------|--------|
| 1 | 기능 명세 불일치 | `analyzer/analyzer.py` | 🔴 높음 |
| 2 | 기능 누락 | `pdf2md/pdf2md.py`, `HTTP_request.py` | 🔴 높음 |
| 3 | 구조적 결함 | `analyzer/analyzer.py`, `pipeline.py` | 🟡 중간 |
| 4 | 로직 미완성 | `Agent/agent.py` | 🟡 중간 |
| 5 | API 오용 | `Discord/chat_gemini.py` | 🟡 중간 |
| 6 | 성능 | `analyzer/analyzer.py` | 🟡 중간 |
| 7 | UX 결함 | `Agent/discord_bot.py` | 🟢 낮음 |
| 8 | 미구현 모듈 | `modules/utils/` | 🟢 낮음 |
| 9 | 코드 정리 | 프로젝트 루트 | 🟢 낮음 |

---

## 1. 🔴 Citation Map 포맷 불일치 (Step 5)

### 문제
`workflow.md`는 Citation Map 형식을 다음과 같이 명시했다.
```
"Section 3.2, 5th paragraph: [Text]"
```
단락 번호까지 포함한 **정확한 위치 추적**이 요구사항이다.

현재 `analyzer.py`의 `_DEEP_DIVE_SYSTEM` 프롬프트는 아래 형식만 생성한다.
```
**[Concept / Claim]**: [Key finding]
```
단락 위치 정보가 전혀 없다.

### 해결 방법
`_DEEP_DIVE_SYSTEM` 프롬프트 수정 + 섹션 콘텐츠에 단락 번호를 붙여 LLM에 전달.

#### Step A — `chunker.py` 수정: `Section` → 단락 번호 삽입 유틸리티 추가
```python
# chunker.py 에 추가
def annotate_paragraphs(section: Section) -> str:
    """섹션 콘텐츠의 각 단락 앞에 번호를 붙여 반환한다.

    출력 예:
        [¶1] Diffusion models have achieved...
        [¶2] However, their computational cost...
    """
    paragraphs = [p.strip() for p in section.content.split("\n\n") if p.strip()]
    numbered = [f"[¶{i+1}] {p}" for i, p in enumerate(paragraphs)]
    return "\n\n".join(numbered)
```

#### Step B — `analyzer.py` 수정: `_DEEP_DIVE_SYSTEM` 프롬프트 변경
```
# 변경 전
**[Concept / Claim]**: [Key finding, data point, or argument]

# 변경 후
- **[Section Title], ¶N**: [Key finding, data point, or argument — traceable to paragraph number]
```

#### Step C — `deep_dive()` 호출부 수정
```python
# analyzer.py deep_dive() 내부
content = annotate_paragraphs(sec)   # ← 단락 번호 삽입
user_msg = f"## {sec.title}\n\n{content}"
```

---

## 2. 🔴 HTML URL 처리 미구현

### 문제
`HTTP_request.md`에 "PDF 또는 HTML 형식일때"를 명시했지만, 현재 `pdf2md.py`는 PDF만 처리한다.
`arxiv.org/abs/xxxx`(HTML 추상 페이지), `semanticscholar.org` 링크 등 입력 시 `fitz.open()` 에서 예외 발생.

### 해결 방법
PDF/HTML 분기 처리 레이어 추가.

#### Step A — `HTTP_request.py` 수정: Content-Type 반환값 확장
```python
# 기존: (bool, str)  →  변경: (bool, str, str)  # (success, url_or_error, content_type)
def parse_and_validate_url(text: str) -> tuple[bool, str, str]:
    """
    Returns (True, url, "pdf"|"html") or (False, error_msg, "")
    """
```

#### Step B — `modules/html2md/html2md.py` 신규 생성
```python
# httpx + BeautifulSoup4 로 HTML → Markdown 변환
def extract_md_from_html(url: str) -> str: ...
```

#### Step C — `pipeline.py` Step 2 분기 추가
```python
# pipeline.py
if content_type == "html":
    md_text = extract_md_from_html(url)
else:
    md_text = extract_md_from_url(url)   # 기존 PDF 경로
```

#### 필요 패키지 추가
```
# requirements.txt
beautifulsoup4
markdownify   # HTML → Markdown 변환 라이브러리
```

---

## 3. 🟡 `split_sections()` 3중 중복 호출

### 문제
`analyzer.py`의 세 함수(`skeleton_scan`, `deep_dive`, `cross_check`)가 각각 `split_sections(md_text)`를 독립적으로 호출한다.
동일한 Markdown 텍스트에 대해 동일한 파싱을 3회 반복 — 순수한 낭비.

### 해결 방법
`pipeline.py` 에서 섹션 파싱을 1회만 수행하고 결과를 전달.

#### Step A — `analyzer.py` 시그니처 변경
```python
# 변경 전
async def skeleton_scan(md_text: str, llm: LLMFn) -> str:
async def deep_dive(md_text: str, llm: LLMFn) -> str:
async def cross_check(md_text: str, llm: LLMFn) -> str:

# 변경 후
async def skeleton_scan(sections: list[Section], llm: LLMFn) -> str:
async def deep_dive(sections: list[Section], llm: LLMFn) -> str:
async def cross_check(sections: list[Section], llm: LLMFn) -> str:
```

#### Step B — `pipeline.py` Step 3을 명시적으로 분리
```python
# pipeline.py
# ── Step 3: 섹션 분리 ─────────────────────────────────────────────────────────
logger.info("[Pipeline] Step 3 — 정규 표현식 챕터 분리")
sections = split_sections(md_text)
logger.info("[Pipeline] 섹션 수: %d", len(sections))

# ── Steps 4-6: 섹션 객체 직접 전달 ────────────────────────────────────────────
skeleton = await skeleton_scan(sections, llm)
dive     = await deep_dive(sections, llm)
check    = await cross_check(sections, llm)
```

---

## 4. 🟡 Agent Tool-Calling 루프가 단발성

### 문제
`agent.py` slow path는 LLM의 tool call을 **단 1회** 처리 후 종료한다.
LLM이 `validate_pdf_url` → `fetch_pdf_as_markdown` → `run_research_pipeline` 순서로 연속 호출이 필요한 경우 처리 불가.

### 해결 방법
`while` 루프로 변경하여 LLM이 더 이상 tool call을 요청하지 않을 때까지 반복.

```python
# agent.py slow path 변경
MAX_TURNS = 6

for _ in range(MAX_TURNS):
    response = await asyncio.to_thread(
        ollama_chat, model=AGENT_MODEL, messages=messages, tools=TOOL_DEFINITIONS
    )
    msg = response.message

    if not msg.tool_calls:
        return msg.content or "[응답 없음]"   # 루프 종료: 최종 답변

    # tool call 처리 (기존 로직 동일)
    messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})
    for tc in msg.tool_calls:
        ...
        messages.append({"role": "tool", "content": tool_result})

return "[최대 반복 횟수 초과. 응답을 완성하지 못했습니다.]"
```

---

## 5. 🟡 Gemini `system_prompt` API 오용

### 문제
`chat_gemini.py`는 system_prompt를 user message에 문자열로 병합한다.
```python
# 현재 (잘못된 방식)
parts = [system_prompt, user_message]
prompt_text = "\n\n".join(parts)
_client.models.generate_content(model=..., contents=prompt_text)
```
Gemini API는 `system_instruction` 파라미터를 공식 지원한다. 섞으면 LLM이 역할을 혼동할 수 있다.

### 해결 방법
```python
# 변경 후
from google.genai import types

config = types.GenerateContentConfig(
    system_instruction=system_prompt if system_prompt else None,
)
_client.models.generate_content(
    model=DEFAULT_MODEL_NAME,
    contents=user_message,
    config=config,
)
```

---

## 6. 🟡 Deep Dive 순차 처리 → 병렬 처리

### 문제
섹션이 많은 논문(8~15 섹션)에서 LLM 호출이 순차로 이루어져 전체 처리 시간이 선형으로 증가.

### 해결 방법
`asyncio.gather()`로 섹션별 LLM 호출을 병렬 실행.

```python
# analyzer.py deep_dive() 변경
async def _analyse_section(sec: Section, llm: LLMFn) -> str:
    content = annotate_paragraphs(sec)
    content = content[:8000] + "\n\n[... 내용 생략 ...]" if len(content) > 8000 else content
    return await llm(f"## {sec.title}\n\n{content}", _DEEP_DIVE_SYSTEM)

async def deep_dive(sections: list[Section], llm: LLMFn) -> str:
    body = get_body_sections(sections)
    if not body:
        return "[Deep Dive: 분석할 본문 섹션을 찾을 수 없습니다.]"

    logger.info("Deep Dive 시작: %d 섹션 (병렬)", len(body))
    results = await asyncio.gather(*[_analyse_section(sec, llm) for sec in body])
    return "\n\n---\n\n".join(results)
```

> **주의**: Ollama는 단일 프로세스이므로 병렬 요청이 큐잉될 수 있다. Gemini/OpenAI 백엔드에서 효과가 크다.

---

## 7. 🟢 Discord 메시지 분할 시 Markdown 파괴

### 문제
`discord_bot.py::_split_text()`가 1990자 단위로 단순 슬라이싱하여
코드 블록(` ``` `), 표(`|`), 헤더(`##`) 가 중간에 잘림.

### 해결 방법
줄 단위(`\n`)로 분할하여 Markdown 블록 경계를 존중하는 방식으로 변경.

```python
def _split_text(text: str, limit: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.splitlines(keepends=True):
        if current_len + len(line) > limit and current:
            chunks.append("".join(current))
            current, current_len = [], 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("".join(current))
    return chunks
```

---

## 8. 🟢 `modules/utils/` 빈 모듈

### 문제
`utils.md`만 있고 `utils.py`가 없다. `__init__.py`도 없어 모듈로 import 불가.

### 해결 방법
공통 유틸리티 함수들을 모아 구현.

```python
# modules/utils/utils.py
"""공통 유틸리티"""

def truncate(text: str, max_chars: int, suffix: str = "\n\n[... 내용 생략 ...]") -> str:
    """텍스트를 max_chars 이하로 자르되 suffix를 붙인다."""
    return text if len(text) <= max_chars else text[:max_chars] + suffix
```

현재 `analyzer.py` 곳곳에 인라인으로 작성된 8000자 자르기 로직을 이 함수로 대체.

---

## 9. 🟢 프로젝트 루트 파일 정리

### 문제
개발/디버깅 중 생성된 임시 파일들이 루트에 방치되어 있다.

```
/Geminitest.py
/OpenAItest.py
/ollama_test.py
/ollama_summary.md
/_inspect_chunks.py
/_inspect_pdf.py
```

### 해결 방법
`tests/` 디렉토리 또는 `scripts/` 디렉토리로 이동하거나 삭제.

```
ResearchAgent/
├── tests/
│   ├── test_gemini.py          ← Geminitest.py 이동
│   ├── test_openai.py          ← OpenAItest.py 이동
│   ├── test_ollama.py          ← ollama_test.py 이동
│   ├── inspect_chunks.py       ← _inspect_chunks.py 이동
│   └── inspect_pdf.py          ← _inspect_pdf.py 이동
└── docs/
    └── ollama_summary.md       ← ollama_summary.md 이동
```

`modules/Discord/test.py`는 구 버전 단순 챗봇으로, ResearchAgent 파이프라인과 무관하다.
`tests/` 로 이동하거나 삭제 여부를 결정할 것.

---

## 10. 최종 작업 순서 (의존 관계 기준)

```
Phase 1 — 구조 기반 작업 (다른 변경에 영향)
  [1] chunker.py: annotate_paragraphs() 추가
  [2] modules/utils/utils.py: truncate() 구현
  [3] analyzer.py: 시그니처를 (md_text) → (sections) 로 변경

Phase 2 — 핵심 기능 수정
  [4] analyzer.py: Citation Map 포맷 수정 (¶N 위치 포함)
  [5] pipeline.py: Step 3 명시적 분리 + sections 전달
  [6] analyzer.py: deep_dive() 병렬 처리

Phase 3 — 기능 추가
  [7] html2md/html2md.py: HTML → Markdown 구현
  [8] HTTP_request.py: content_type 반환 추가
  [9] pipeline.py: HTML/PDF 분기 추가

Phase 4 — 개선 및 수정
  [10] agent.py: tool-calling while 루프 변경
  [11] chat_gemini.py: system_instruction 파라미터 사용
  [12] discord_bot.py: _split_text() 줄 단위 분할

Phase 5 — 정리
  [13] 루트 임시 파일 → tests/ 이동
  [14] modules/Discord/test.py 정리
```

---

## 변경 후 예상 디렉토리 구조

```
ResearchAgent/
├── Agent/
│   ├── agent.py          # tool-calling 루프 개선
│   ├── pipeline.py       # Step 3 명시적 분리
│   ├── discord_bot.py    # _split_text() 개선
│   ├── cli.py
│   └── tools.py
├── modules/
│   ├── HTTP_request/
│   │   └── HTTP_request.py   # content_type 반환 추가
│   ├── pdf2md/
│   │   └── pdf2md.py
│   ├── html2md/              # 신규
│   │   ├── __init__.py
│   │   └── html2md.py
│   ├── chunker/
│   │   └── chunker.py        # annotate_paragraphs() 추가
│   ├── analyzer/
│   │   └── analyzer.py       # 시그니처/프롬프트/병렬화 수정
│   ├── Discord/
│   │   ├── chat_gemini.py    # system_instruction 수정
│   │   ├── chat_openai.py
│   │   └── chat_ollama.py
│   └── utils/
│       ├── __init__.py
│       └── utils.py          # truncate() 구현
└── tests/
    ├── test_chunker.py
    ├── test_pipeline.py
    └── ...                   # 루트 임시 파일 이동
```
