from modules.ai.evaluation.context_ab import (
    ContextScenarioObservation,
    evaluate_context_scenario,
)


def test_context_ab_covers_profile_memory_and_unconfirmed_policy() -> None:
    observations = [
        ContextScenarioObservation(
            scenario="A_without_profile", usefulness=0.25, latency_ms=4, tokens=20
        ),
        ContextScenarioObservation(
            scenario="B_confirmed_profile",
            claimed_evidence_refs=["fixture://profile/confirmed-sheets"],
            confirmed_evidence_refs=["fixture://profile/confirmed-sheets"],
            usefulness=0.75,
            latency_ms=6,
            tokens=38,
        ),
        ContextScenarioObservation(
            scenario="C_profile_and_rag",
            claimed_evidence_refs=[
                "fixture://profile/confirmed-sheets",
                "fixture://memory/confirmed-service-project",
            ],
            confirmed_evidence_refs=[
                "fixture://profile/confirmed-sheets",
                "fixture://memory/confirmed-service-project",
            ],
            usefulness=1.0,
            latency_ms=9,
            tokens=61,
        ),
        ContextScenarioObservation(
            scenario="D_with_unconfirmed_items",
            claimed_evidence_refs=["fixture://profile/confirmed-sheets"],
            confirmed_evidence_refs=["fixture://profile/confirmed-sheets"],
            unconfirmed_evidence_refs=["fixture://memory/unconfirmed-leadership"],
            usefulness=0.75,
            latency_ms=10,
            tokens=70,
        ),
    ]

    measured = {item.scenario: evaluate_context_scenario(item) for item in observations}

    assert measured["C_profile_and_rag"]["evidence_precision"] == 1.0
    assert measured["C_profile_and_rag"]["usefulness"] > measured["A_without_profile"]["usefulness"]
    assert measured["D_with_unconfirmed_items"]["unconfirmed_fact_rate"] == 0.0
    assert measured["D_with_unconfirmed_items"]["unsupported_claim_rate"] == 0.0
    assert (
        measured["D_with_unconfirmed_items"]["tokens"] > measured["B_confirmed_profile"]["tokens"]
    )
