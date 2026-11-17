from __future__ import annotations

import pytest
from PySide6.QtWidgets import QToolButton, QWidget

from MyVideoExplorer.tag_cloud.tag_util import (
    VALID_NAME_PATTERN,
    get_contrast_text_color,
    style_painter_button,
    validate_name,
    validate_tag_name,
)

# -- Color and styling tests --


def test_get_contrast_text_color_should_return_dark_text_for_light_background():
    assert get_contrast_text_color("#ffffff") == "#000000"
    assert get_contrast_text_color("#ffff00") == "#000000"


def test_get_contrast_text_color_should_return_light_text_for_dark_background():
    assert get_contrast_text_color("#000000") == "#ffffff"
    assert get_contrast_text_color("#112233") == "#ffffff"


def test_get_contrast_text_color_should_fallback_for_invalid_color():
    assert get_contrast_text_color("invalid-color") == "#000000"


def test_style_painter_button_should_set_custom_style(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    button = QToolButton(parent)

    style_painter_button(button, "#ff5500")
    assert button.property("preserve_custom_style") is True
    assert "background-color: #ff5500" in button.styleSheet()


# -- validate_name tests --


@pytest.mark.parametrize(
    "name",
    [
        "Action",
        "SciFi123",
        "Alpha Renamed",
        "My Filter",
        "My-Filter",
        "test_123",
        "a!b@c#",
        "name(with)parens",
        "tag|pipe",
        "x^y&z",
        "a{b}c",
        "[brackets]",
        "a,b",
        "a.b",
        "a:b",
        "a+b",
        "a~b",
        "a*b",
        "a=b",
        "---",
        "___",
    ],
)
def test_validate_name_should_accept_valid_names(name):
    assert validate_name(name) == (True, "")


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        ("path/to", "forward slash"),
        ("back\\slash", "backslash"),
        ("it's", "single quote"),
        ('say "hello"', "double quote"),
    ],
)
def test_validate_name_should_reject_special_chars(name, reason):
    is_valid, msg = validate_name(name)
    assert is_valid is False
    assert "Name may only contain" in msg


@pytest.mark.parametrize("name", ["", "   "])
def test_validate_name_should_reject_empty_and_whitespace(name):
    is_valid, msg = validate_name(name)
    assert is_valid is False
    assert "cannot be empty" in msg


@pytest.mark.parametrize(
    "name",
    [
        "name\twith\ttabs",
        "name\nwith\nnewlines",
    ],
)
def test_validate_name_should_reject_control_characters(name):
    is_valid, _ = validate_name(name)
    assert is_valid is False


# -- validate_tag_name tests --


@pytest.mark.parametrize(
    "name",
    ["Action", "SciFi123", "Sci-Fi", "tag_pipe"],
)
def test_validate_tag_name_should_accept_valid_names(name):
    assert validate_tag_name(name) == (True, "")


@pytest.mark.parametrize("name", ["", "   "])
def test_validate_tag_name_should_reject_empty_and_whitespace(name):
    is_valid, msg = validate_tag_name(name)
    assert is_valid is False
    assert "cannot be empty" in msg


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        ("Sci/Fi", "forward slash"),
        ("tag's", "single quote"),
    ],
)
def test_validate_tag_name_should_reject_special_chars(name, reason):
    is_valid, _ = validate_tag_name(name)
    assert is_valid is False


# -- VALID_NAME_PATTERN tests --


@pytest.mark.parametrize(
    "pattern",
    ["Action", "My-Filter_123", "a!b@c#"],
)
def test_valid_name_pattern_should_match_valid_patterns(pattern):
    assert VALID_NAME_PATTERN.fullmatch(pattern) is not None


@pytest.mark.parametrize(
    "pattern",
    ["path/to", "it's", ""],
)
def test_valid_name_pattern_should_not_match_invalid_patterns(pattern):
    assert VALID_NAME_PATTERN.fullmatch(pattern) is None
