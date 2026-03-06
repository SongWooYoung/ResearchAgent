import os

import discord
from dotenv import load_dotenv

from modules.Discord.chat_gemini import generate_reply as generate_reply_gemini
from modules.Discord.chat_openai import generate_reply as generate_reply_openai
from modules.Discord.chat_ollama import generate_reply as generate_reply_ollama


load_dotenv()

intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용을 읽을 수 있게 설정

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    # 자기 자신이 보낸 메시지에는 반응하지 않기
    if message.author == client.user:
        return

    content = message.content.strip()

    backend = None
    user_input = ""

    # 1) Gemini: !chat-gemini ...
    gemini_prefix = "!chat-gemini "
    # 2) OpenAI: !chat-openai ...  (오타 방지를 위해 !chat-open ai 도 허용)
    openai_prefix = "!chat-openai "
    openai_prefix_with_space = "!chat-open ai "
    # 3) Ollama: !chat-ollama ...
    ollama_prefix = "!chat-ollama "

    if content.startswith(gemini_prefix):
        backend = "gemini"
        user_input = content[len(gemini_prefix) :].strip()
    elif content.startswith(openai_prefix):
        backend = "openai"
        user_input = content[len(openai_prefix) :].strip()
    elif content.startswith(openai_prefix_with_space):
        backend = "openai"
        user_input = content[len(openai_prefix_with_space) :].strip()
    elif content.startswith(ollama_prefix):
        backend = "ollama"
        user_input = content[len(ollama_prefix) :].strip()
    else:
        # 다른 메시지는 무시
        return

    if not user_input:
        await message.channel.send("질문 내용을 입력해 주세요.")
        return

    if backend == "gemini":
        backend_label = "Gemini"
    elif backend == "openai":
        backend_label = "OpenAI"
    else:
        backend_label = "Ollama"

    # LLM이 응답을 생성하는 동안 표시할 메시지
    thinking_message = await message.channel.send(
        f"{backend_label} LLM is generating OUTPUT...\n"
    )

    # 선택된 백엔드로 LLM 응답 생성
    try:
        if backend == "gemini":
            reply_text = await generate_reply_gemini(user_input)
        elif backend == "openai":
            reply_text = await generate_reply_openai(user_input)
        else:  # ollama
            reply_text = await generate_reply_ollama(user_input)
    except Exception as e:
        reply_text = f"{backend_label} LLM 호출 중 오류가 발생했습니다: {e}"

    # 같은 메시지를 LLM 응답으로 교체
    await thinking_message.edit(content=reply_text)


if __name__ == "__main__":
    # 이 파일은 프로젝트 루트에서 아래처럼 실행하는 것을 권장합니다:
    # python -m modules.Discord.test
    client.run(os.getenv("Discord_Bot_Token"))