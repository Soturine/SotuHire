from streamlit.testing.v1 import AppTest


def test_complete_demo_runs_locally_without_gemini():
    app = AppTest.from_file("app.py").run(timeout=30)
    demo = next(button for button in app.button if button.label == "Rodar demo completa")

    app = demo.click().run(timeout=30)

    assert not app.exception
    assert app.session_state["resume_profile"].name == "Camila Torres Andrade"
    assert app.session_state["job_posting"].title == "Engenheiro de Software Júnior"
    assert app.session_state["analysis_result"].provider == "local"
    assert app.session_state["tailor_output"] is not None
