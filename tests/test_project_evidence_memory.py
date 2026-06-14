from modules.memory import CareerMemory, MemoryStore
from modules.portfolio import ProjectAnalysisPayload, analyze_project


def test_project_report_becomes_retrievable_job_evidence(tmp_path):
    memory = CareerMemory(MemoryStore(tmp_path / "memory.jsonl"))
    report = analyze_project(
        ProjectAnalysisPayload(
            url="https://github.example/example/api",
            title="API Example",
            page_type="github_repo",
            readme_text="FastAPI Python SQL API",
            files_sampled=["README.md", "src/api.py", "tests/test_api.py"],
            languages=["Python", "SQL"],
        )
    )

    items = memory.remember_project_analysis(report)
    evidence = memory.retriever.retrieve("vaga Python FastAPI SQL", top_k=10)

    assert {item.kind for item in items} == {
        "github_repo",
        "project_evidence",
        "commit_analysis",
        "readme_analysis",
    }
    assert any(item.kind == "project_evidence" for item in evidence)
