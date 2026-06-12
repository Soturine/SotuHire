"""Streamlit entry point for the SotuHire guided workflow."""

from dotenv import load_dotenv
from modules.ui.pages import render_app

load_dotenv()


if __name__ == "__main__":
    render_app()
