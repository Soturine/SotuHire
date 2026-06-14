from modules.schemas.job_analysis import JobAnalysisSchema
from modules.storage.local_store import LocalStore
from modules.tracker.dashboard import rank_applied_requirements
from modules.tracker.job_tracker import JobTracker


def test_tracker_saves_collection_method_and_deduplicates_existing_applications(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))

    first = tracker.add_existing_application(
        job_title="Backend Junior",
        company="Example",
        source_url="https://jobs.example/view/123?tracking=one",
        collection_method="browser_assisted_capture",
        requirements=["Python", "SQL"],
    )
    duplicate = tracker.add_existing_application(
        job_title="Backend Junior",
        company="Example",
        source_url="https://jobs.example/view/123?tracking=two",
        collection_method="browser_assisted_capture",
        requirements=["Python", "SQL"],
    )

    assert duplicate.id == first.id
    assert len(tracker.list_analyses()) == 1
    assert first.collection_method == "browser_assisted_capture"
    assert first.requirements == ["Python", "SQL"]
    assert first.source_domains == ["jobs.example"]


def test_tracker_merges_prior_application_with_later_sotuhire_analysis(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    prior = tracker.add_existing_application(
        job_title="Pessoa Desenvolvedora Python",
        company="Example",
        source_url="https://jobs.example/123",
    )
    analysis = JobAnalysisSchema(
        match_score=80,
        ats_score=75,
        opportunity_fit_score=80,
        risk_score=10,
        recommendation="apply",
    )

    later = tracker.add_analysis(
        analysis,
        job_title="Pessoa Desenvolvedora Python",
        company="Example",
        source_url="https://jobs.example/123?tracking=sotuhire",
        privacy_acknowledged=True,
        requirements=["Python", "SQL"],
    )

    assert prior.id == later.id
    assert later.status.value == "applied"
    assert later.analysis.match_score == 80
    assert len(tracker.list_analyses()) == 1


def test_tracker_merges_same_job_across_linkedin_and_gupy_like_portals(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))

    linkedin = tracker.add_existing_application(
        job_title="Analista Python Jr",
        company="Example Tech",
        source_url="https://linkedin.example/jobs/view/123",
    )
    gupy = tracker.add_existing_application(
        job_title="Analista de Python Junior",
        company="Example Tech",
        source_url="https://example.gupy.test/jobs/abc",
        requirements=["Python", "SQL"],
    )

    assert linkedin.id == gupy.id
    assert len(tracker.list_analyses()) == 1
    assert gupy.source_domains == ["linkedin.example", "example.gupy.test"]
    assert len(gupy.source_urls) == 2
    assert gupy.requirements == ["Python", "SQL"]


def test_rank_applied_requirements_counts_only_applied_jobs(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    tracker.add_existing_application(
        job_title="Backend",
        company="Example",
        source_url="https://jobs.example/1",
        requirements=["Python", "SQL"],
    )
    tracker.add_existing_application(
        job_title="Dados",
        company="Example",
        source_url="https://jobs.example/2",
        requirements=["python", "Power BI"],
    )

    ranking = dict(rank_applied_requirements(tracker.list_analyses()))
    assert ranking["Python"] == 2
    assert ranking["SQL"] == 1
    assert ranking["Power BI"] == 1
