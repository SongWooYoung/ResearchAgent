import os
from dotenv import load_dotenv # 추가
from openai import OpenAI

load_dotenv() # .env 파일을 읽어서 os.environ에 등록해주는 역할

# 이제 os.getenv가 None이 아닌 실제 키를 가져옵니다.
api_key = os.getenv("OpenAI_API_KEY") 
client = OpenAI(api_key=api_key)

# 2. 클라이언트에 키를 직접 전달
client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-5-mini-2025-08-07", # 혹은 "gpt-3.5-turbo"
    messages=[{"role": "user", "content": "안녕!"}]
)

print(response.choices[0].message.content)