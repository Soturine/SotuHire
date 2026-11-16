"""One owner for the credential-field deny-list used before payloads reach a provider or a store.

Four API services each carried a copy of this check; two of them blocked ``headers`` and two did
not. These tests pin the shared behaviour and that every boundary uses the shared function.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from modules.security import contains_secret_field
from modules.security.credentials import SECRET_FIELD_MARKERS

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = ("profile", "public_exams", "radar", "sources")


@pytest.mark.parametrize("marker", sorted(SECRET_FIELD_MARKERS))
def test_each_marker_is_rejected_at_any_depth_and_case(marker):
    assert contains_secret_field({marker: "x"})
    assert contains_secret_field({"outer": [{"inner": {f"X_{marker.upper()}_Y": 1}}]})
    assert contains_secret_field([({marker: None},)])


def test_ordinary_payloads_pass():
    payload = {
        "text": "Pessoa enfermeira com COREN ativo",
        "source_type": "pdf",
        "evidence": [{"title": "Plantão UTI", "tags": ["saúde"]}],
        "language": "pt-BR",
    }
    assert not contains_secret_field(payload)
    # values are not keys: a credential-looking value is the job of contains_provider_secret
    assert not contains_secret_field({"text": "my api_key is in this sentence"})
    assert not contains_secret_field("token")
    assert not contains_secret_field(None)


def test_request_headers_are_rejected_on_every_boundary():
    assert contains_secret_field({"metadata": {"headers": {"Accept": "text/html"}}})


@pytest.mark.parametrize("module", BOUNDARIES)
def test_each_api_boundary_uses_the_shared_check_and_keeps_no_local_copy(module):
    source = (ROOT / "apps" / "api" / "services" / f"{module}.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    local = [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and "secret" in node.name.lower()
    ]
    assert local == [], f"{module} redefines a secret check: {local}"
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "contains_secret_field"
    ]
    assert calls, f"{module} no longer checks payload keys before its boundary"
