"""
Chunker module unit test — no LLM required.
Run: python -m modules.chunker.test
"""
from modules.chunker.chunker import (
    split_sections,
    get_abstract,
    get_intro,
    get_conclusion,
    get_body_sections,
)

# ── Sample academic paper markdown ──────────────────────────────────────────
SAMPLE_MD = """\
## Abstract
This paper proposes Adaptive Feature Alignment (AFA), a novel method for efficient
diffusion models. AFA reduces inference cost by 40% while achieving state-of-the-art
FID scores on FFHQ and LSUN benchmarks.

## 1 Introduction
Diffusion models have recently achieved remarkable results in image generation.
However, their computational cost remains prohibitive for many applications.
We hypothesize that aligning features between adjacent timesteps can significantly
reduce inference cost without sacrificing image quality.

## 2 Related Work
Previous work on efficient diffusion includes DDIM (Song et al., 2020) and DDPM.
These methods focus on step reduction rather than feature alignment.
Our approach is complementary and can be combined with step-reduction techniques.

## 3 Method
### 3.1 Adaptive Feature Alignment (AFA)
The AFA module computes cross-attention between feature maps at adjacent timesteps.
This alignment signal is used to prune redundant computations.

### 3.2 Feature Alignment Loss (FAL)
We introduce FAL loss to supervise the alignment process during training.
FAL encourages temporally consistent feature representations.

## 4 Experiments
We evaluate on FFHQ 256×256, LSUN-Church, and CIFAR-10.
FFHQ FID: 3.2 (baseline 3.8). LSUN-Church FID: 4.1 (baseline 5.0).
Inference speed: 40% faster on A100 GPU.

## 5 Conclusion
We proposed AFA for efficient diffusion models. Experiments confirm the hypothesis:
feature alignment reduces inference cost by 40% while improving FID scores.
Future work will explore AFA in video diffusion settings.

## References
[1] Song et al., 2020. Denoising Diffusion Implicit Models. NeurIPS.
[2] Ho et al., 2020. Denoising Diffusion Probabilistic Models. NeurIPS.
"""


def main() -> None:
    print("=" * 50)
    print("Chunker Module Test")
    print("=" * 50)

    sections = split_sections(SAMPLE_MD)
    print(f"\n총 섹션 수: {len(sections)}\n")
    for s in sections:
        print(f"  [level={s.level}] {s.title!r:40s}  ({len(s.content):4d} chars)")

    # ── Individual accessors ─────────────────────────────────────────────────
    print("\n--- Abstract (첫 100자) ---")
    abstract = get_abstract(sections)
    assert abstract is not None, "Abstract not found!"
    print(abstract[:100])

    print("\n--- Introduction (첫 100자) ---")
    intro = get_intro(sections)
    assert intro is not None, "Introduction not found!"
    print(intro[:100])

    print("\n--- Conclusion (첫 100자) ---")
    conclusion = get_conclusion(sections)
    assert conclusion is not None, "Conclusion not found!"
    print(conclusion[:100])

    print("\n--- Body sections ---")
    body = get_body_sections(sections)
    assert len(body) > 0, "Body sections not found!"
    for s in body:
        print(f"  {s.title!r}")

    # ── Numbered-section fallback ────────────────────────────────────────────
    numbered_md = """\
1 Introduction\nDiffusion models are powerful.\n\n2 Method\nWe propose AFA.\n\n3 Experiments\nResults show improvements.\n\n4 Conclusion\nWe demonstrated AFA works.\n"""
    num_sections = split_sections(numbered_md)
    assert len(num_sections) >= 4, f"Expected ≥4 sections, got {len(num_sections)}"
    print(f"\n번호 섹션 테스트: {len(num_sections)}개 섹션 인식됨 ✓")

    print("\n✅ Chunker Test 전체 통과\n")


if __name__ == "__main__":
    main()
