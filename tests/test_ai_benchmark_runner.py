import json
import os
import subprocess
import sys

from modules.ai.provider_errors import (
    ProviderCallError,
    ProviderError,
    ProviderErrorCategory,
)
from scripts.run_ai_benchmark import _run_diagnostic


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


def test_provider_diagnostic_suite_emits_auditable_status(tmp_path) -> None:
    output = tmp_path / "diagnostic.json"
    env = {
        **os.environ,
        "SOTUHIRE_BENCHMARK_DATABASE": str(tmp_path / "diagnostic.db"),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_ai_benchmark.py",
            "--suite",
            "provider-diagnostic",
            "--providers",
            "local",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["results"][0]["status"] == "valid"
    assert report["results"][0]["case_id"] == "provider-diagnostic-local"
    assert "sanitized_message" in report["results"][0]


def test_provider_diagnostic_marks_account_block_without_hiding_it() -> None:
    class BlockedProvider:
        model = "gpt-4.1-mini"
        last_call_metadata: dict[str, object] = {}

        def ping(self) -> str:
            raise ProviderCallError(
                ProviderError(
                    provider="openai",
                    model=self.model,
                    status_code=429,
                    error_code="insufficient_quota",
                    error_type="insufficient_quota",
                    category=ProviderErrorCategory.INSUFFICIENT_QUOTA,
                    retryable=False,
                    request_id="req_safe",
                    sanitized_message="Quota unavailable.",
                )
            )

    result = _run_diagnostic("openai", BlockedProvider(), "benchmark-test")

    assert result["status"] == "BLOCKED_EXTERNAL_ACCOUNT"
    assert result["error_category"] == "INSUFFICIENT_QUOTA"
    assert result["request_id"] == "req_safe"
    assert result["metrics"]["diagnostic_success"] == 0
