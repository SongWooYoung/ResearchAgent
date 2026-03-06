import re
from typing import Tuple

import requests
from urllib.parse import urlparse


HTTPS_URL_PATTERN = re.compile(r"https://[^\s<>\"']+")


def extract_https_url(text: str) -> str | None:
    """
    임의의 입력 문자열에서 https 로 시작하는 첫 번째 URL을 추출한다.
    """
    match = HTTPS_URL_PATTERN.search(text)
    if not match:
        return None
    return match.group(0)


def validate_pdf_url(url: str) -> Tuple[bool, str]:
    """
    주어진 URL이 https 로 시작하는 유효한 PDF 링크인지 서버에 HEAD 요청을 보내 확인한다.

    .. deprecated::
        parse_and_validate_url() 사용을 권장한다. content_type을 함께 반환한다.
    """
    ok, result, _ = parse_and_validate_url(url)
    return ok, result


def parse_and_validate_url(text: str) -> Tuple[bool, str, str]:
    """입력 문자열에서 URL을 파싱하고 유효성을 검증한다.

    Returns:
        (True,  url,        "pdf" | "html")  — 성공
        (False, error_msg,  "")              — 실패

    PDF/HTML 판별 기준:
        1. Content-Type 헤더가 application/pdf → "pdf"
        2. URL 경로가 .pdf 로 끝남           → "pdf"
        3. 그 외 (text/html 등)              → "html"
    """
    url = extract_https_url(text)
    if not url:
        return False, "입력에서 https로 시작하는 URL을 찾을 수 없습니다.", ""

    try:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            return False, "https로 시작하는 올바른 URL 형식이 아닙니다.", ""

        response = requests.head(url, allow_redirects=True, timeout=5)

        if response.status_code != 200:
            return False, f"접근할 수 없는 페이지입니다. (Status: {response.status_code})", ""

        content_type = response.headers.get("Content-Type", "").lower()

        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            return True, url, "pdf"

        return True, url, "html"

    except requests.exceptions.RequestException as e:
        return False, f"연결 오류가 발생했습니다: {str(e)}", ""


# 하위 호환성 유지 (pipeline.py 이전 버전 참조용)
def parse_and_validate_pdf_url(text: str) -> Tuple[bool, str]:
    """.. deprecated:: parse_and_validate_url() 사용 권장."""
    ok, result, _ = parse_and_validate_url(text)
    return ok, result
