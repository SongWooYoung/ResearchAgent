"""공통 유틸리티."""


def truncate(text: str, max_chars: int, suffix: str = "\n\n[... 내용 생략 ...]") -> str:
    """텍스트를 max_chars 이하로 자르되 suffix를 붙인다."""
    return text if len(text) <= max_chars else text[:max_chars] + suffix
