1. 입력 -> URL(https 로 시작하는 문자 파싱) -> HTTP_request에서 URL 확인 
    if 정상  -> URL 반환
    else    -> error message 

    # 여기서 든 의문 : genenral 한 케이스를 볼때 입력이 URL이 아닌 경우가 올 수 있는데 이런 경우 모든 경우를 하드 코딩 해야 하는가?
        Gemini 왈 : ollama에 내가 갖고 있는 tools를 주고, system prompt에 역할을 명시한 이후, message와 비교해서 LLM이 tool calls를 하는지 안하는지에 따라서 호출 하던 말던 하면 된다.

2. 입력된 URL -> PDF -> 마크다운으로 변환
    pymupdf4llm 고려중

3. 정규 표현식으로 챕터별 분리
4. **Skeleton Scan (초안):** Abstract + Intro를 분석하여 논문의 '지도'를 그립니다.
5. **Deep Dive (본문):** 각 섹션별로 내용을 요약하되, **"Citation Map"** 기능을 추가합니다. (예: "Section 3.2, 5th paragraph: [Text]" 형식 유지 강제)
6. **Cross-Check (검증):** 전체 흐름을 확인하며 Intro의 가설이 Conclusion에서 증명되었는지 대조합니다.