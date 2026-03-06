from ollama import chat

# qwen3.5:9b
# qwen3.5:27b
# ------- 위는 수동으로 업뎃해야 해서 후보로만 -----------

# qwen3:4b
# qwen3:14b
# qwen3:30b

# llama3:8b
# llama3.2:3b

# gemma3:12b  # 가용 가능 한 모델 중에 benchmark 성능이 좋을 뿐더러 크기도 작음 

response = chat(
    model='gemma3:12b',
    messages=[{'role': 'user', 'content': 'Hello!'}],
)
print(response.message.content)