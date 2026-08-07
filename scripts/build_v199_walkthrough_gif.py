"""Build the optimized v1.9.9 document-to-application walkthrough GIF."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "docs" / "assets" / "screenshots"
TARGET = SCREENSHOTS / "sotuhire-v1.9.9-document-to-application-walkthrough.gif"
FRAMES = [
    "sotuhire-v1.9.9-import-pdf.png",
    "sotuhire-v1.9.9-block-review.png",
    "sotuhire-v1.9.9-provenance.png",
    "sotuhire-v1.9.9-master-resume.png",
    "sotuhire-v1.9.9-application-analysis-bundle.png",
    "sotuhire-v1.9.9-requirement-unknown.png",
    "sotuhire-v1.9.9-application-variant-diff.png",
    "sotuhire-v1.9.9-professional-assets.png",
    "sotuhire-v1.9.9-application-kit-review.png",
    "sotuhire-v1.9.9-resume-preview.png",
    "sotuhire-v1.9.9-pdf-export.png",
    "sotuhire-v1.9.9-docx-export.png",
    "sotuhire-v1.9.9-tracker-review.png",
    "sotuhire-v1.9.9-stale-analysis.png",
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
        duration=1400,
        loop=0,
        optimize=True,
        disposal=2,
    )
    for frame in frames:
        frame.close()
    print(f"created {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
