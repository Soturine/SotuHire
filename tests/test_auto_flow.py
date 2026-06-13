from streamlit.testing.v1 import AppTest


def test_quick_mode_runs_the_complete_example_without_preferences():
    app = AppTest.from_file("app.py").run(timeout=30)
    example_button = next(
        button for button in app.button if button.label == "Rodar análise de exemplo"
    )

    app = example_button.click().run(timeout=30)

    assert app.session_state["resume_text"]
    assert app.session_state["job_text"]
    assert app.session_state["analysis_result"] is not None
    assert app.session_state["tailor_output"] is not None
    assert not app.exception
