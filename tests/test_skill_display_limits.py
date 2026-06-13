from modules.ui.components import split_visible_items


def test_primary_skill_display_is_limited_and_preserves_remaining_items():
    skills = [f"Skill {index}" for index in range(12)]

    primary, secondary = split_visible_items(skills, visible_limit=8)

    assert len(primary) == 8
    assert len(secondary) == 4
    assert [*primary, *secondary] == skills
