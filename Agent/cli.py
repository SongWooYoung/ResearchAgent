"""
Research Agent — CLI runner for testing without Discord.

Usage:
    python -m Agent.cli "https://arxiv.org/pdf/2410.09016"
    python -m Agent.cli --backend gemini "https://arxiv.org/pdf/2410.09016"
    python -m Agent.cli --backend openai "Diffusion model이 뭔가요?"
    python -m Agent.cli --pipeline-only "https://arxiv.org/pdf/2410.09016"
"""
import argparse
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


async def _run(user_input: str, backend: str, pipeline_only: bool) -> None:
    if pipeline_only:
        from modules.llm import get_llm
        from Agent.pipeline import run_pipeline
        result = await run_pipeline(user_input, get_llm(backend))
    else:
        from Agent.agent import run_agent
        result = await run_agent(user_input, backend)

    print(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Agent CLI")
    parser.add_argument("input", help="논문 URL 또는 질문")
    parser.add_argument(
        "--backend", default="ollama",
        choices=["ollama", "gemini", "openai"],
        help="LLM 백엔드 선택 (기본: ollama)",
    )
    parser.add_argument(
        "--pipeline-only", action="store_true",
        help="agent 라우팅 없이 파이프라인만 직접 실행",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.input, args.backend, args.pipeline_only))


if __name__ == "__main__":
    main()
