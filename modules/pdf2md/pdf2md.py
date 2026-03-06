import requests
import fitz  # PyMuPDF
import pymupdf4llm


def extract_md_from_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        doc = fitz.open(stream=response.content, filetype="pdf")
        md_text = pymupdf4llm.to_markdown(doc)
        doc.close()
        return md_text

    except Exception as e:
        return f"변환 중 오류 발생: {e}"

# 결과물은 바로 LLM에게 던질 수 있는 깨끗한 Markdown입니다