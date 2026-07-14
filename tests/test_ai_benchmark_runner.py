import json
import os
import subprocess
import sys


def _run(tmp_path, *args: str):
    output = tmp_path / "report.json"
    env = {
        **os.environ,
        "SOTUHIRE_BENCHMARK_DATABASE": str(tmp_path / "benchmarks.db"),
    }
    command = [
        sys.executable,
        "scripts/run_ai_benchmark.py",
        "--suite",
        "mock",
        "--output",
        str(output),
        *args,
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
    return completed, output


def test_benchmark_runner_is_seeded_sanitized_and_resumable(tmp_path) -> None:
    first, output = _run(tmp_path, "--seed", "42", "--max-cases", "2")
    assert first.returncode == 0, first.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    case_ids = [item["case_id"] for item in report["results"]]
    assert len(case_ids) == 2
    assert '"input":' not in json.dumps(report).casefold()

    resumed, _ = _run(tmp_path, "--seed", "42", "--max-cases", "2", "--resume")
    assert resumed.returncode == 0, resumed.stderr
    resumed_report = json.loads(output.read_text(encoding="utf-8"))
    assert [item["case_id"] for item in resumed_report["results"]] == case_ids
