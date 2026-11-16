from modules.portfolio.file_sampler import prioritize_paths


def test_prioritize_readme():
    paths = ["src/app.py", "README.md", "random.bin"]
    assert prioritize_paths(paths)[0] == "README.md"
