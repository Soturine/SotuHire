from modules.portfolio.file_sampler import prioritize_paths
from modules.portfolio.portfolio_score import calculate_portfolio_score


def test_prioritize_readme():
    paths = ["src/app.py", "README.md", "random.bin"]
    assert prioritize_paths(paths)[0] == "README.md"


def test_portfolio_score():
    assert calculate_portfolio_score(100, 50, 80, 70) is not None
