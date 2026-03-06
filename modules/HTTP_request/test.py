from .HTTP_request import (
    extract_https_url,
    validate_pdf_url,
    parse_and_validate_pdf_url,
)


def run_case(description: str, text: str) -> None:
    ok, result = parse_and_validate_pdf_url(text)
    status = "OK " if ok else "ERR"
    print(f"[{status}] {description}")
    print(f"  input : {text}")
    print(f"  result: {result}")
    print()


def main() -> None:
    # 1. 정상적인 arXiv PDF URL
    run_case(
        "정상 PDF URL",
        "이 논문 한번 봐줘: https://arxiv.org/pdf/2410.09016.pdf",
    )

    # 2. URL 이 전혀 없는 입력
    run_case(
        "URL 없음",
        "이 문장은 URL 을 포함하지 않습니다.",
    )

    # 3. http 로 시작하는 URL (https 아님)
    run_case(
        "http URL",
        "http://example.com/sample.pdf",
    )

    # 4. PDF 가 아닌 URL
    run_case(
        "PDF 아님",
        "https://example.com/index.html",
    )


if __name__ == "__main__":
    main()

