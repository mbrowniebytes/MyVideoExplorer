from PySide6.QtWidgets import QToolButton, QWidget

from MyVideoExplorer.tag_cloud.tag_util import (
    get_contrast_text_color,
    style_painter_button,
    validate_tag_name,
)


def test_get_contrast_text_color():
    # Light backgrounds require dark text
    assert get_contrast_text_color("#ffffff") == "#000000"
    assert get_contrast_text_color("#ffff00") == "#000000"

    # Dark backgrounds require light text
    assert get_contrast_text_color("#000000") == "#ffffff"
    assert get_contrast_text_color("#112233") == "#ffffff"

    # Invalid color fallback
    assert get_contrast_text_color("invalid-color") == "#000000"


def test_style_painter_button(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    button = QToolButton(parent)

    style_painter_button(button, "#ff5500")
    assert button.property("preserve_custom_style") is True
    assert "background-color: #ff5500" in button.styleSheet()


def test_validate_tag_name():
    assert validate_tag_name("Action") == (True, "")
    assert validate_tag_name("SciFi123") == (True, "")

    is_valid, msg = validate_tag_name("")
    assert is_valid is False
    assert "cannot be empty" in msg

    is_valid, msg = validate_tag_name("   ")
    assert is_valid is False
    assert "cannot be empty" in msg

    is_valid, msg = validate_tag_name("Sci-Fi!")
    assert is_valid is False
    assert "alphanumeric" in msg
