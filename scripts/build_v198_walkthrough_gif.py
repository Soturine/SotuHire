"""Build the optimized v1.9.8 product walkthrough GIF from release screenshots."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "docs" / "assets" / "screenshots"
TARGET = SCREENSHOTS / "sotuhire-v1.9.8-guided-application-walkthrough.gif"
FRAMES = [
    "sotuhire-v1.9.8-application-lab-start.png",
    "sotuhire-v1.9.8-profile-evidence.png",
    "sotuhire-v1.9.8-master-resume.png",
    "sotuhire-v1.9.8-job-snapshot.png",
    "sotuhire-v1.9.8-analysis-progress.png",
    "sotuhire-v1.9.8-readiness-report.png",
    "sotuhire-v1.9.8-suggestions.png",
    "sotuhire-v1.9.8-variant-diff.png",
    "sotuhire-v1.9.8-resume-studio.png",
    "sotuhire-v1.9.8-resume-preview.png",
    "sotuhire-v1.9.8-application-kit.png",
    "sotuhire-v1.9.8-action-plan.png",
    "sotuhire-v1.9.8-tracker-saved.png",
    "sotuhire-v1.9.8-ai-quality.png",
]


def main() -> None:
    frames: list[Image.Image] = []
    for name in FRAMES:
        with Image.open(SCREENSHOTS / name) as source:
            resized = source.convert("RGB").resize((960, 667), Image.Resampling.LANCZOS)
            frames.append(resized.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    first, *rest = frames
    first.save(
        TARGET,
        save_all=True,
        append_images=rest,
        duration=1200,
        loop=0,
        optimize=True,
        disposal=2,
    )
    for frame in frames:
        frame.close()
    print(f"created {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
