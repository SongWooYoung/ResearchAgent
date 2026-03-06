"""HTML URL을 Markdown으로 변환한다.

requests로 페이지를 가져온 뒤 BeautifulSoup으로 본문을 추출하고
markdownify로 Markdown 텍스트를 생성한다.

학술 페이지(arxiv abstract, semanticscholar 등)를 주요 대상으로 한다.
"""
import requests
from bs4 import BeautifulSoup
import markdownify


# 제거할 태그 (사이드바, 내비게이션, 광고 등 본문 외 요소)
_REMOVE_TAGS = ["nav", "header", "footer", "script", "style", "aside", "noscript"]


def extract_md_from_html(url: str) -> str:
    """HTML 페이지를 다운로드하고 Markdown으로 변환한다.

    Returns:
        변환된 Markdown 문자열. 실패 시 "변환 중 오류 발생: ..." 형식의 문자열.
    """
    try:
        response = requests.get(url, timeout=30, headers={"User-Agent": "ResearchAgent/1.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 본문 외 요소 제거
        for tag in soup.find_all(_REMOVE_TAGS):
            tag.decompose()

        # 본문 컨테이너 우선 탐색 (없으면 body 전체 사용)
        body = (
            soup.find("article")
            or soup.find("main")
            or soup.find(id="content")
            or soup.find(class_="content")
            or soup.body
        )

        if body is None:
            return "변환 중 오류 발생: HTML에서 본문을 찾을 수 없습니다."

        md_text = markdownify.markdownify(str(body), heading_style="ATX", strip=["a"])
        # 연속 빈 줄을 최대 2줄로 압축
        import re
        md_text = re.sub(r"\n{3,}", "\n\n", md_text).strip()

        return md_text

    except Exception as e:
        return f"변환 중 오류 발생: {e}"
