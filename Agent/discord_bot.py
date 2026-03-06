"""
Research Agent — Discord Bot

Commands:
    !research <URL or question>     — auto-route (URL → pipeline, else → chat)
    !research-gemini  <...>         — force Gemini backend
    !research-openai  <...>         — force OpenAI backend
    !research-ollama  <...>         — force Ollama backend

Run:
    python -m Agent.discord_bot
"""
import logging
import os

import discord
from dotenv import load_dotenv

from Agent.agent import run_agent

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Discord client ────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Prefix → backend mapping (longest first to avoid prefix collision)
_PREFIXES: list[tuple[str, str]] = [
    ("!research-gemini ", "gemini"),
    ("!research-openai ", "openai"),
    ("!research-ollama ", "ollama"),
    ("!research ",        "ollama"),
]

_DISCORD_LIMIT = 1990  # leave a small buffer below 2000


@bot.event
async def on_ready() -> None:
    logger.info("ResearchAgent bot logged in as %s", bot.user)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return

    content = message.content.strip()
    backend: str | None = None
    user_input: str | None = None

    for prefix, bk in _PREFIXES:
        if content.startswith(prefix):
            backend = bk
            user_input = content[len(prefix):].strip()
            break

    if user_input is None:
        return  # not addressed to this bot

    if not user_input:
        await message.channel.send("분석할 논문 URL 또는 질문을 입력해 주세요.")
        return

    thinking = await message.channel.send(
        "🔍 ResearchAgent가 분석 중입니다… (수십 초 소요될 수 있습니다)"
    )

    try:
        result = await run_agent(user_input, backend)
    except Exception as exc:
        logger.exception("Agent 실행 오류")
        result = f"❌ 오류 발생: {exc}"

    if len(result) <= _DISCORD_LIMIT:
        await thinking.edit(content=result)
    else:
        await thinking.edit(content="📋 분석 완료. 결과를 분할 전송합니다…")
        for chunk in _split_text(result, _DISCORD_LIMIT):
            await message.channel.send(chunk)


def _split_text(text: str, limit: int) -> list[str]:
    """줄 단위로 텍스트를 분할하여 Markdown 블록 경계를 존중한다."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.splitlines(keepends=True):
        if current_len + len(line) > limit and current:
            chunks.append("".join(current))
            current, current_len = [], 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("".join(current))
    return chunks


if __name__ == "__main__":
    token = os.getenv("Discord_Bot_Token")
    if not token:
        raise RuntimeError("Discord_Bot_Token 환경 변수가 설정되지 않았습니다.")
    bot.run(token)
