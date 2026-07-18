"""Keyboard helper tests."""

from manik_bot.bot.keyboards import get_id_choice_menu


def test_get_id_choice_menu_builds_numeric_buttons() -> None:
    """Check ID choice keyboard layout."""
    keyboard = get_id_choice_menu([1, 2, 3, 4])

    rows = keyboard.keyboard

    assert [button.text for button in rows[0]] == ["1", "2", "3"]
    assert [button.text for button in rows[1]] == ["4"]
    assert [button.text for button in rows[2]] == ["Назад"]
