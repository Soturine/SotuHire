import json

import pytest
from modules.storage.migrations import MigrationRunner
from modules.storage.repositories import JsonlRepository, JsonRepository, SqliteRepository


@pytest.fixture(
    params=["json", "jsonl", "sqlite"],
)
def repository(request, tmp_path):
    if request.param == "json":
        return JsonRepository(tmp_path / "records.json")
    if request.param == "jsonl":
        return JsonlRepository(tmp_path / "records.jsonl")
    database = tmp_path / "sotuhire.db"
    MigrationRunner(database).apply(create_backup=False)
    return SqliteRepository("profiles", database_path=database)


def test_repository_contract_create_read_filter_update_delete(repository):
    repository.save({"id": "one", "name": "Primeiro", "status": "active"})
    repository.save({"id": "two", "name": "Segundo", "status": "inactive"})

    assert repository.exists("one")
    assert repository.get("one")["name"] == "Primeiro"
    assert [item["id"] for item in repository.list(filters={"status": "active"})] == ["one"]

    repository.save({"id": "one", "name": "Atualizado", "status": "active"})
    assert repository.get("one")["name"] == "Atualizado"
    assert repository.delete("one") is True
    assert repository.delete("one") is False
    assert repository.get("one") is None


def test_jsonl_repository_surfaces_corruption(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text(json.dumps({"id": "one"}) + "\n{invalid", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        JsonlRepository(path).list()
