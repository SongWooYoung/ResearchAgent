"""
Analyzer module test — calls a real LLM backend.
Run:
    python -m modules.analyzer.test                    # default: ollama
    python -m modules.analyzer.test --backend gemini
    python -m modules.analyzer.test --backend openai
"""
import argparse
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SAMPLE_MD = """\
## Abstract
This paper proposes Adaptive Feature Alignment (AFA), a novel method for efficient
diffusion models. AFA reduces inference cost by 40% while achieving state-of-the-art
FID scores on FFHQ and LSUN benchmarks.

## 1 Introduction
Diffusion models are powerful generative models but computationally expensive.
We hypothesize that aligning features between adjacent timesteps can significantly
reduce inference cost without sacrificing image quality.

## 2 Related Work
DDIM and DDPM focus on step reduction. Our approach operates at the feature level
and is orthogonal to step-reduction methods. Previous alignment work in transformers
inspires our design.

## 3 Method
We introduce the AFA module, which applies cross-attention across timestep features.
The Feature Alignment Loss (FAL) supervises training to produce temporally consistent
feature representations.

## 4 Experiments
FFHQ 256 FID: 3.2 (baseline 3.8). LSUN-Church FID: 4.1 (baseline 5.0).
Inference speed measured on A100 GPU showed a 40% reduction in compute.

## 5 Conclusion
We proposed AFA for efficient diffusion models. Our experiments confirm that
feature alignment reduces inference cost by 40% while maintaining or improving
FID scores, validating the original hypothesis.
"""


async def _run(backend: str) -> None:
    from modules.analyzer.analyzer import skeleton_scan, cross_check

    if backend == "gemini":
        from modules.Discord.chat_gemini import generate_reply as llm
    elif backend == "openai":
        from modules.Discord.chat_openai import generate_reply as llm
    else:
        from modules.Discord.chat_ollama import generate_reply as llm

    print(f"=== Analyzer Test  (backend: {backend}) ===\n")

    print("─" * 40)
    print("Step 4 — Skeleton Scan")
    print("─" * 40)
    skeleton = await skeleton_scan(SAMPLE_MD, llm)
    print(skeleton)

    print("\n" + "─" * 40)
    print("Step 6 — Cross-Check")
    print("─" * 40)
    check = await cross_check(SAMPLE_MD, llm)
    print(check)

    print("\n✅ Analyzer Test 완료\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="ollama",
                        choices=["ollama", "gemini", "openai"])
    args = parser.parse_args()
    asyncio.run(_run(args.backend))


if __name__ == "__main__":
    main()
