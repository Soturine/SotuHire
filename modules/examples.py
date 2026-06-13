"""Safe loaders for fictitious examples shipped with the repository."""

from __future__ import annotations

from pathlib import Path

EXAMPLES_ROOT = Path("examples")
DEFAULT_RESUME_EXAMPLE = "resumes/rafael_like_engineering_resume.txt"
DEFAULT_JOB_EXAMPLE = "jobs/junior_software_engineer.txt"


def load_example(relative_path: str) -> str:
    """Load a repository example while preventing paths outside examples/."""
    root = EXAMPLES_ROOT.resolve()
    target = (root / relative_path).resolve()
    if root not in target.parents or target.suffix.lower() not in {".txt", ".json"}:
        raise ValueError("Exemplo inválido.")
    return target.read_text(encoding="utf-8")


def load_default_resume_example() -> str:
    """Return the default fictitious resume example."""
    return load_example(DEFAULT_RESUME_EXAMPLE)


def load_default_job_example() -> str:
    """Return the default fictitious vacancy example."""
    return load_example(DEFAULT_JOB_EXAMPLE)
