from modules.ui.components import (
    block_items,
    csv_items,
    display_value,
    line_items,
    modality_label,
    seniority_label,
)


def test_ui_converts_unknown_and_empty_values_to_portuguese():
    assert display_value("unknown") == "Não informado"
    assert display_value("") == "Não informado"
    assert display_value(None) == "Não informado"
    assert modality_label("unknown") == "Não informado"


def test_ui_translates_internal_labels():
    assert modality_label("remote") == "Remoto"
    assert modality_label("hybrid") == "Híbrido"
    assert seniority_label("junior") == "Júnior"
    assert seniority_label("senior") == "Sênior"


def test_ui_edit_helpers_remove_duplicates_and_blank_items():
    assert csv_items("Python, React, Python, ") == ["Python", "React"]
    assert line_items("Experiência A\n\n- Experiência B\nExperiência A") == [
        "Experiência A",
        "Experiência B",
    ]
    assert block_items("Cargo A\nDescrição A\n\nCargo B\nDescrição B") == [
        "Cargo A\nDescrição A",
        "Cargo B\nDescrição B",
    ]
