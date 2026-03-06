"""
Integration test — full Agent pipeline with a real arXiv PDF.

Run:
    python -m Agent.test                     # default Ollama backend
    python -m Agent.test --backend gemini
    python -m Agent.test --backend openai
    python -m Agent.test --skip-download     # use cached sample MD (no network)
"""
import argparse
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# AFA paper used throughout development
TEST_URL = "https://arxiv.org/pdf/2410.09016"

# Minimal offline markdown for --skip-download mode
_OFFLINE_MD = """\
## Abstract
Adaptive Feature Alignment (AFA) reduces diffusion model inference by 40% with
state-of-the-art FID on FFHQ and LSUN.

## 1 Introduction
Diffusion models are powerful but slow. We hypothesize that aligning features
across timesteps reduces inference cost without quality loss.

## 2 Related Work
DDIM and DDPM target step reduction; AFA targets feature-level efficiency,
making the two approaches orthogonal.

## 3 Method
The AFA module applies cross-attention between adjacent-timestep feature maps.
Feature Alignment Loss (FAL) supervises training.

## 4 Experiments
FFHQ FID: 3.2 vs 3.8 baseline. Inference: 40% faster on A100.

## 5 Conclusion
AFA validates the original hypothesis: feature alignment cuts inference cost
by 40% while maintaining or improving FID scores.
"""


async def _run(backend: str, skip_download: bool) -> None:
    if backend == "gemini":
        from modules.Discord.chat_gemini import generate_reply as llm
    elif backend == "openai":
        from modules.Discord.chat_openai import generate_reply as llm
    else:
        from modules.Discord.chat_ollama import generate_reply as llm

    print(f"{'=' * 55}")
    print(f"  Integration Test  |  backend: {backend}")
    print(f"{'=' * 55}\n")

    if skip_download:
        print("[OFFLINE MODE — using built-in sample markdown]\n")
        from modules.analyzer.analyzer import skeleton_scan, deep_dive, cross_check

        skeleton = await skeleton_scan(_OFFLINE_MD, llm)
        dive = await deep_dive(_OFFLINE_MD, llm)
        check = await cross_check(_OFFLINE_MD, llm)

        report = (
            f"# 📄 논문 분석 리포트 (Offline Sample)\n\n"
            f"---\n\n"
            f"## 🗺️ Skeleton Scan\n\n{skeleton}\n\n"
            f"---\n\n"
            f"## 🔬 Deep Dive\n\n{dive}\n\n"
            f"---\n\n"
            f"## ✅ Cross-Check\n\n{check}"
        )
    else:
        print(f"[ONLINE MODE — downloading: {TEST_URL}]\n")
        from Agent.pipeline import run_pipeline
        report = await run_pipeline(f"이 논문 분석해줘: {TEST_URL}", llm)

    print(report)
    print(f"\n{'=' * 55}")
    print("✅ Integration Test 완료")
    print(f"{'=' * 55}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Agent integration test")
    parser.add_argument("--backend", default="ollama",
                        choices=["ollama", "gemini", "openai"])
    parser.add_argument("--skip-download", action="store_true",
                        help="네트워크 없이 내장 샘플 MD로 테스트")
    args = parser.parse_args()
    asyncio.run(_run(args.backend, args.skip_download))


if __name__ == "__main__":
    main()
