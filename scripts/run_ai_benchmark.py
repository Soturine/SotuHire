"""Run reproducible, sanitized AI evaluation suites over fictitious golden cases."""

# ruff: noqa: E402 -- executable script bootstraps the repository root before local imports.

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ai.benchmark_store import AiBenchmark, AiBenchmarkResult, AiBenchmarkStore
from modules.ai.evaluation.dataset import GoldenCase, iter_golden_cases
from modules.ai.evaluation.metrics import hallucination_rate, normalized_exact_match
from modules.ai.providers import GeminiProvider, MockProvider, OpenAIProvider
from modules.ai.schemas.analysis_insights import WishlistDraftOutput
from modules.ai.structured_analysis import analyze_structured
from modules.ai.structured_job_extractor import extract_structured_job
from modules.ai.structured_resume_extractor import extract_structured_resume
from modules.ai.task_registry import default_ai_task_registry
from modules.public_exams import PublicExamImportInput, PublicExamService
from modules.radar.wishlist_draft import build_local_wishlist_draft

APP_VERSION = "1.9.7"
DATASET_VERSION = "v1.9.7-1"
EXTERNAL_CALL_CAP = 20
RELEASE_SMOKE_CALL_CAP = 10


def main() -> int:
    args = _parser().parse_args()
    cases = _select_cases(args)
    providers = _resolve_providers(args.providers, args.suite)
    if not providers:
        print(json.dumps({"status": "skipped", "reason": "no providers available"}))
        return 0
    generated_id = _benchmark_id(args.seed, args.suite)
    output_path = Path(args.output or f"benchmarks/results/{generated_id}.json")
    previous = _load_previous(output_path) if args.resume else {}
    benchmark_id = str(previous.get("benchmark_run_id") or generated_id)
    registry = default_ai_task_registry()
    prompt_versions = {task.prompt_id: task.prompt_version for task in registry.list()}
    run = AiBenchmark(
        benchmark_run_id=benchmark_id,
        git_sha=_git_sha(),
        app_version=APP_VERSION,
        suite=args.suite,
        providers=providers,
        models=_parse_list(args.models),
        prompt_versions=prompt_versions,
        seed=args.seed,
        dataset_version=DATASET_VERSION,
        environment="external_opt_in" if any(p != "local" for p in providers) else "local",
    )
    store = AiBenchmarkStore(os.getenv("SOTUHIRE_BENCHMARK_DATABASE", "benchmarks/ai-quality.db"))
    store.save_run(run)
    results: list[dict[str, Any]] = list(previous.get("results", []))
    completed = {
        (item.get("case_id"), item.get("provider"), item.get("model", "")) for item in results
    }
    provider_calls: dict[str, int] = {provider: 0 for provider in providers}
    for provider_name in providers:
        provider = _provider(provider_name, args.models)
        model = str(getattr(provider, "model", "local"))
        cap = RELEASE_SMOKE_CALL_CAP if args.suite == "release-smoke" else EXTERNAL_CALL_CAP
        for case in cases:
            if (case.case_id, provider_name, model) in completed:
                continue
            if provider_name != "local" and provider_calls[provider_name] >= cap:
                break
            result = _run_case(case, provider_name, provider, benchmark_id)
            provider_calls[provider_name] += int(provider_name != "local")
            store.save_result(AiBenchmarkResult.model_validate(result))
            results.append(_public_result(result))
            _write_report(output_path, run, results)
    finished = datetime.now(UTC)
    run = run.model_copy(update={"finished_at": finished, "status": "completed"})
    store.save_run(run)
    report = _write_report(output_path, run, results)
    regressions = _regressions(report, providers) if args.fail_on_regression else []
    print(json.dumps(_console_summary(report, output_path, regressions), ensure_ascii=False))
    return 1 if regressions else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        required=True,
        choices=["mock", "local", "release-smoke", "golden", "adversarial", "full"],
    )
    parser.add_argument("--providers", default="local")
    parser.add_argument("--models", default="")
    parser.add_argument("--tasks", default="")
    parser.add_argument("--domains", default="")
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--seed", type=int, default=197)
    parser.add_argument("--output", default="")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--fail-on-regression", action="store_true")
    return parser


def _select_cases(args: argparse.Namespace) -> list[GoldenCase]:
    cases = iter_golden_cases(ROOT / "tests" / "golden")
    tasks, domains = set(_parse_list(args.tasks)), set(_parse_list(args.domains))
    if tasks:
        cases = [case for case in cases if case.task_id in tasks]
    if domains:
        cases = [case for case in cases if case.domain in domains]
    if args.suite == "adversarial":
        cases = [case for case in cases if any(tag != "golden" for tag in case.tags)]
    random.Random(args.seed).shuffle(cases)
    if args.max_cases > 0:
        cases = cases[: args.max_cases]
    return cases


def _resolve_providers(raw: str, suite: str) -> list[str]:
    requested = _parse_list(raw)
    if requested == ["available"]:
        requested = ["local"]
        if os.getenv("SOTUHIRE_TEST_GEMINI_API_KEY"):
            requested.append("gemini")
        if os.getenv("SOTUHIRE_TEST_OPENAI_API_KEY"):
            requested.append("openai")
    if suite in {"mock", "local", "golden", "adversarial"}:
        requested = [provider for provider in requested if provider == "local"] or ["local"]
    allowed = {"local", "gemini", "openai"}
    return list(dict.fromkeys(provider for provider in requested if provider in allowed))


def _provider(name: str, raw_models: str) -> object | None:
    models = _model_map(raw_models)
    if name == "gemini":
        key = os.getenv("SOTUHIRE_TEST_GEMINI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("Gemini opt-in key is not present")
        return GeminiProvider(api_key=key, model=models.get("gemini", "gemini-2.5-flash"))
    if name == "openai":
        key = os.getenv("SOTUHIRE_TEST_OPENAI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("OpenAI opt-in key is not present")
        return OpenAIProvider(api_key=key, model=models.get("openai", "gpt-4.1-mini"))
    return None


def _run_case(
    case: GoldenCase, provider_name: str, provider: object | None, benchmark_id: str
) -> dict[str, Any]:
    task = default_ai_task_registry().get(case.task_id)
    started = time.perf_counter()
    schema_valid = False
    error_type = ""
    output: dict[str, Any] = {}
    try:
        if provider_name == "local":
            model = _local_output(case)
        else:
            model = provider.generate_structured(_prompt(task.prompt_id), case.input)  # type: ignore[union-attr]
        validated = task.output_schema.model_validate(model)
        output = validated.model_dump(mode="json")
        schema_valid = True
    except Exception as exc:
        error_type = type(exc).__name__
    latency_ms = round((time.perf_counter() - started) * 1000)
    metadata = getattr(provider, "last_call_metadata", {}) if provider is not None else {}
    if not isinstance(metadata, dict):
        metadata = {}
    strings = _strings(output)
    expected = list(case.expected_fields.values())
    completion = (
        sum(
            any(normalized_exact_match(value, candidate) for candidate in strings)
            for value in expected
        )
        / len(expected)
        if expected
        else 0.0
    )
    unsupported = hallucination_rate(strings, case.forbidden_claims)
    evidence_refs = set(_find_refs(output))
    required_refs = set(case.required_evidence_refs)
    evidence_precision = (
        len(evidence_refs & required_refs) / len(evidence_refs) if evidence_refs else None
    )
    metrics: dict[str, float | int | bool | None] = {
        "schema_validity": float(schema_valid),
        "required_field_completion": completion,
        "unsupported_claim_rate": unsupported,
        "hallucination_rate": unsupported,
        "evidence_precision": evidence_precision,
        "prompt_injection_resistance": float(
            not any(
                tag in case.tags
                for tag in ("prompt_injection", "document_ignore_rules", "malicious_content")
            )
            or unsupported == 0
        ),
    }
    return AiBenchmarkResult(
        benchmark_run_id=benchmark_id,
        case_id=case.case_id,
        task_id=case.task_id,
        domain=case.domain,
        provider=provider_name,
        model=str(getattr(provider, "model", "local")),
        prompt_id=task.prompt_id,
        prompt_version=task.prompt_version,
        metrics=metrics,
        latency_ms=int(metadata.get("latency_ms") or latency_ms),
        input_tokens=_int_or_none(metadata.get("input_tokens")),
        output_tokens=_int_or_none(metadata.get("output_tokens")),
        total_tokens=_int_or_none(metadata.get("total_tokens")),
        estimated_cost=_float_or_none(metadata.get("estimated_cost")),
        fallback_used=False,
        schema_valid=schema_valid,
        error_type=error_type,
    ).model_dump(mode="json")


def _local_output(case: GoldenCase) -> object:
    task = default_ai_task_registry().get(case.task_id)
    data = case.input
    if case.task_id == "resume_extraction":
        return extract_structured_resume(
            str(data.get("resume_text", "")), provider=MockProvider()
        ).output
    if case.task_id == "job_extraction":
        return extract_structured_job(str(data.get("job_text", "")), provider=MockProvider()).output
    if case.task_id == "match_explanation":
        return analyze_structured(
            str(data.get("resume_text", "")),
            str(data.get("job_text", "")),
            provider=MockProvider(),
        ).analysis
    if case.task_id == "wishlist_builder":
        return WishlistDraftOutput.model_validate(
            build_local_wishlist_draft(str(data.get("free_text", ""))).model_dump()
        )
    if case.task_id == "public_exam_extraction":
        payload = PublicExamImportInput(
            text=str(data.get("text", "")), source_url=str(data.get("source_ref", ""))
        )
        return PublicExamService().draft_local(payload)
    return task.output_schema.model_validate({})


def _prompt(prompt_id: str):
    from modules.ai.prompt_loader import default_prompt_registry

    return default_prompt_registry().get(prompt_id)


def _write_report(path: Path, run: AiBenchmark, results: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate = _aggregate(results)
    report = {
        "benchmark_run_id": run.benchmark_run_id,
        "git_sha": run.git_sha,
        "app_version": run.app_version,
        "suite": run.suite,
        "providers": run.providers,
        "models": run.models,
        "prompt_versions": run.prompt_versions,
        "seed": run.seed,
        "dataset_version": run.dataset_version,
        "environment": run.environment,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else "",
        "status": run.status,
        "aggregate": aggregate,
        "results": results,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return report


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    overall = _aggregate_group(results)
    providers = sorted({str(item.get("provider", "")) for item in results})
    tasks = sorted({str(item.get("task_id", "")) for item in results})
    return {
        **overall,
        "by_provider": {
            provider: _aggregate_group(
                [item for item in results if item.get("provider") == provider]
            )
            for provider in providers
            if provider
        },
        "by_task": {
            task: _aggregate_group([item for item in results if item.get("task_id") == task])
            for task in tasks
            if task
        },
    }


def _aggregate_group(results: list[dict[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, list[float]] = {}
    for result in results:
        for name, value in result.get("metrics", {}).items():
            if isinstance(value, int | float) and not isinstance(value, bool):
                metrics.setdefault(name, []).append(float(value))
    count = len(results)
    cost_values = [
        float(item["estimated_cost"])
        for item in results
        if isinstance(item.get("estimated_cost"), int | float)
    ]
    token_values = [
        int(item["total_tokens"]) for item in results if isinstance(item.get("total_tokens"), int)
    ]
    return {
        "cases": len(results),
        **{name: mean(values) for name, values in sorted(metrics.items()) if values},
        "latency_p50_ms": _percentile(
            [float(item["latency_ms"]) for item in results if item.get("latency_ms") is not None],
            0.5,
        ),
        "latency_p95_ms": _percentile(
            [float(item["latency_ms"]) for item in results if item.get("latency_ms") is not None],
            0.95,
        ),
        "tokens_input": sum(int(item.get("input_tokens") or 0) for item in results),
        "tokens_output": sum(int(item.get("output_tokens") or 0) for item in results),
        "estimated_cost": sum(cost_values) if len(cost_values) == count else None,
        "estimated_cost_coverage": len(cost_values) / count if count else 0.0,
        "token_usage_coverage": len(token_values) / count if count else 0.0,
        "fallback_rate": (
            sum(bool(item.get("fallback_used")) for item in results) / count if count else 0.0
        ),
        "provider_error_rate": (
            sum(bool(item.get("error_type")) for item in results) / count if count else 0.0
        ),
        "timeout_rate": (
            sum("timeout" in str(item.get("error_type", "")).lower() for item in results) / count
            if count
            else 0.0
        ),
    }


def _regressions(report: dict[str, Any], providers: list[str]) -> list[str]:
    regressions: list[str] = []
    for provider in providers:
        baseline = ROOT / "benchmarks" / "baselines" / f"v1.9.7-{provider}.json"
        if not baseline.exists():
            continue
        expected = json.loads(baseline.read_text(encoding="utf-8"))
        thresholds = expected.get("thresholds", {})
        aggregate = report["aggregate"].get("by_provider", {}).get(provider, {})
        for name, rule in thresholds.items():
            if name not in aggregate or not isinstance(rule, dict):
                continue
            if "min" in rule and aggregate[name] < rule["min"]:
                regressions.append(f"{provider}:{name} below minimum")
            if "max" in rule and aggregate[name] > rule["max"]:
                regressions.append(f"{provider}:{name} above maximum")
    return regressions


def _public_result(result: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "result_id",
        "benchmark_run_id",
        "case_id",
        "task_id",
        "domain",
        "provider",
        "model",
        "prompt_id",
        "prompt_version",
        "metrics",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "estimated_cost",
        "fallback_used",
        "schema_valid",
        "error_type",
        "created_at",
    }
    return {key: value for key, value in result.items() if key in allowed}


def _console_summary(
    report: dict[str, Any], output: Path, regressions: list[str]
) -> dict[str, Any]:
    return {
        "benchmark_run_id": report["benchmark_run_id"],
        "suite": report["suite"],
        "providers": report["providers"],
        "aggregate": report["aggregate"],
        "output": str(output),
        "regressions": regressions,
    }


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _strings(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in _strings(nested)]
    return [str(value)] if value is not None else []


def _find_refs(value: object) -> list[str]:
    return [item for item in _strings(value) if item.startswith("fixture://")]


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _model_map(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in _parse_list(value):
        if ":" in item:
            provider, model = item.split(":", 1)
            result[provider] = model
    return result


def _benchmark_id(seed: int, suite: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{suite}-{seed}"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _load_previous(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = round((len(values) - 1) * quantile)
    return values[index]


def _int_or_none(value: object) -> int | None:
    if not isinstance(value, str | int | float | bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: object) -> float | None:
    if not isinstance(value, str | int | float | bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
