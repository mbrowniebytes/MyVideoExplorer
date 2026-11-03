from PySide6.QtWidgets import QToolButton, QWidget

from MyVideoExplorer.tag_cloud.tag_util import (
    VALID_NAME_PATTERN,
    get_contrast_text_color,
    style_painter_button,
    validate_name,
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


def test_validate_name_accepts_valid_names():
    # Alphanumeric names
    assert validate_name("Action") == (True, "")
    assert validate_name("SciFi123") == (True, "")

    # Names with spaces
    assert validate_name("Alpha Renamed") == (True, "")
    assert validate_name("My Filter") == (True, "")

    # Names with allowed special characters
    assert validate_name("My-Filter") == (True, "")
    assert validate_name("test_123") == (True, "")
    assert validate_name("a!b@c#") == (True, "")
    assert validate_name("name(with)parens") == (True, "")
    assert validate_name("tag|pipe") == (True, "")
    assert validate_name("x^y&z") == (True, "")
    assert validate_name("a{b}c") == (True, "")
    assert validate_name("[brackets]") == (True, "")
    assert validate_name("a,b") == (True, "")
    assert validate_name("a.b") == (True, "")
    assert validate_name("a:b") == (True, "")
    assert validate_name("a+b") == (True, "")
    assert validate_name("a~b") == (True, "")
    assert validate_name("a*b") == (True, "")
    assert validate_name("a=b") == (True, "")

    # Names with only special characters
    assert validate_name("---") == (True, "")
    assert validate_name("___") == (True, "")


def test_validate_name_rejects_slashes():
    is_valid, msg = validate_name("path/to")
    assert is_valid is False
    assert "Name may only contain" in msg

    is_valid, msg = validate_name("back\\slash")
    assert is_valid is False


def test_validate_name_rejects_quotes():
    is_valid, msg = validate_name("it's")
    assert is_valid is False

    is_valid, msg = validate_name('say "hello"')
    assert is_valid is False


def test_validate_name_rejects_empty_and_whitespace():
    is_valid, msg = validate_name("")
    assert is_valid is False
    assert "cannot be empty" in msg

    is_valid, msg = validate_name("   ")
    assert is_valid is False
    assert "cannot be empty" in msg


def test_validate_name_rejects_control_characters():
    is_valid, msg = validate_name("name\twith\ttabs")
    assert is_valid is False

    is_valid, msg = validate_name("name\nwith\nnewlines")
    assert is_valid is False


def test_validate_tag_name_uses_shared_regex():
    # Alphanumeric names are valid
    assert validate_tag_name("Action") == (True, "")
    assert validate_tag_name("SciFi123") == (True, "")

    # Names with allowed special characters are now valid (extended from alphanumeric-only)
    assert validate_tag_name("Sci-Fi") == (True, "")
    assert validate_tag_name("tag_pipe") == (True, "")

    # Empty names are rejected
    is_valid, msg = validate_tag_name("")
    assert is_valid is False
    assert "cannot be empty" in msg

    is_valid, msg = validate_tag_name("   ")
    assert is_valid is False
    assert "cannot be empty" in msg

    # Names with slashes are rejected
    is_valid, msg = validate_tag_name("Sci/Fi")
    assert is_valid is False

    # Names with quotes are rejected
    is_valid, msg = validate_tag_name("tag's")
    assert is_valid is False


def test_valid_name_pattern():
    # Valid patterns
    assert VALID_NAME_PATTERN.fullmatch("Action")
    assert VALID_NAME_PATTERN.fullmatch("My-Filter_123")
    assert VALID_NAME_PATTERN.fullmatch("a!b@c#")

    # Invalid patterns
    assert VALID_NAME_PATTERN.fullmatch("path/to") is None
    assert VALID_NAME_PATTERN.fullmatch("it's") is None
    assert VALID_NAME_PATTERN.fullmatch("") is None
