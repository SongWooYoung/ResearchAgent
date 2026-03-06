import os
from dotenv import load_dotenv # 추가
from google import genai

load_dotenv()

def main() -> None:
    # 1. API 키 설정
    api_key = os.getenv("Gemini_API_KEY")
    if not api_key:
        raise RuntimeError("API 키가 설정되지 않았습니다.")

    # 2. 클라이언트 초기화
    client = genai.Client(api_key=api_key)

    print("--- 응답 시작 ---")
    
    try:
        # 3. 모델명을 'gemini-2.0-flash'로 시도 (현재 가장 권장되는 최신 속도형 모델)
        # 만약 이것도 안된다면 'gemini-1.5-flash' (앞에 models/ 없이)로 적어보세요.
        responses = client.models.generate_content_stream(
            model="gemini-2.5-flash", 
            contents="AI가 어떻게 작동하는지 한 문장으로 알려줘.",
        )

        for chunk in responses:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                
    except Exception as e:
        print(f"\n에러 발생: {e}")
        print("\n팁: 'gemini-2.0-flash'가 안되면 'gemini-1.5-flash'로 다시 시도해보세요.")

    print("\n--- 응답 완료 ---")

if __name__ == "__main__":
    main()