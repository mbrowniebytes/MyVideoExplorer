from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLineEdit, QToolButton

from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.settings.settings_tags import SettingsTagsTab
from MyVideoExplorer.tag_cloud.tag_cloud_settings import TagCloudSettings
from MyVideoExplorer.theme.theme import APP_THEME


def test_tag_settings_edits_and_deletes_are_saved_immediately(
    qtbot, tmp_path, monkeypatch
):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    for name in (
        "SETTINGS_STATE_FILE",
        "SETTINGS_APP_FILE",
        "SETTINGS_UI_FILE",
        "SETTINGS_MEDIA_FILE",
        "SETTINGS_FILTER_FILE",
    ):
        monkeypatch.setattr(
            f"MyVideoExplorer.settings.settings_state.{name}",
            cfg_dir / f"{name.removeprefix('SETTINGS_').lower()}.json",
        )
    for name in (
        "DEFAULTS_STATE_FILE",
        "DEFAULTS_APP_FILE",
        "DEFAULTS_UI_FILE",
        "DEFAULTS_MEDIA_FILE",
        "DEFAULTS_FILTER_FILE",
    ):
        monkeypatch.setattr(
            f"MyVideoExplorer.settings.settings_state.{name}",
            cfg_dir / "defaults" / f"{name.removeprefix('DEFAULTS_').lower()}.json",
        )
    monkeypatch.setattr("MyVideoExplorer.settings.settings_state.CFG_DIR", cfg_dir)
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_state.PACKAGE_CFG_DIR",
        cfg_dir / "defaults",
    )
    state = SettingsState(MagicMock())
    store = DbTags(state, tmp_path / "tag_catalog.db")
    store.replace_catalog(
        [
            {"tag": "Favorite", "color": "#ff0000"},
            {"tag": "Comedy", "color": "#00ff00"},
        ],
        {},
        [],
    )
    widget = TagCloudSettings(state, store)
    qtbot.addWidget(widget)
    cloud_set_tags = MagicMock(wraps=widget.cloud.set_tags)
    monkeypatch.setattr(widget.cloud, "set_tags", cloud_set_tags)
    state.tag_counts_changed.emit()
    cloud_set_tags.assert_called_once()

    initial_chip = next(
        chip for tag, chip in widget.cloud._tag_widgets if tag["tag"] == "Favorite"
    )
    initial_label = initial_chip.findChild(QToolButton)
    assert initial_label is not None
    assert "background-color: #ff0000" in initial_label.styleSheet()
    assert "padding: 3px 5px; }" in initial_label.styleSheet()
    initial_style = initial_label.styleSheet()
    APP_THEME.apply_standard_widget_styles(initial_label)
    assert initial_label.styleSheet() == initial_style

    favorite_chip = next(
        chip for tag, chip in widget.cloud._tag_widgets if tag["tag"] == "Favorite"
    )
    favorite_button = favorite_chip.findChild(QToolButton)
    assert favorite_button is not None
    qtbot.mouseDClick(favorite_button, Qt.MouseButton.LeftButton)
    name_edit = favorite_chip.findChild(QLineEdit)
    assert name_edit is not None
    name_edit.setText("MustWatch")
    monkeypatch.setattr(
        "MyVideoExplorer.tag_cloud.tag_cloud_widget.QColorDialog.getColor",
        lambda *_args: QColor("#112233"),
    )
    color_button = favorite_chip.findChild(QToolButton, "edit_tag_color_inline")
    save_button = favorite_chip.findChild(QToolButton, "save_tag_edit")
    assert color_button is not None and save_button is not None
    color_button.click()
    save_button.click()
    assert store.list_tags() == [
        {"tag": "Comedy", "color": "#00ff00"},
        {"tag": "MustWatch", "color": "#112233"},
    ]
    assert state.tags == store.list_tags()

    comedy_chip = next(
        chip for tag, chip in widget.cloud._tag_widgets if tag["tag"] == "Comedy"
    )
    delete_button = next(
        button
        for button in comedy_chip.findChildren(QToolButton)
        if button.toolTip() == "Delete Comedy"
    )
    assert not delete_button.icon().isNull()
    assert delete_button.iconSize().width() == 14
    assert delete_button.property("preserve_custom_style")
    assert "border: 0" in delete_button.styleSheet()
    delete_button.click()

    assert store.list_tags() == [{"tag": "MustWatch", "color": "#112233"}]
    assert state.tags == store.list_tags()

    store.add_catalog_tag("CreatedFromMedia")
    assert any(tag["tag"] == "CreatedFromMedia" for tag in widget.cloud.tags)


def test_tag_cloud_filter_and_sort(qtbot):
    from MyVideoExplorer.tag_cloud.tag_cloud_widget import TagCloudWidget

    cloud = TagCloudWidget(
        [
            {"tag": "Comedy", "color": "#00ff00", "qty": 2},
            {"tag": "Favorite", "color": "#ff0000", "qty": 9},
            {"tag": "Drama", "color": "#0000ff", "qty": 4},
        ],
        editable=True,
        selectable=True,
    )
    qtbot.addWidget(cloud)

    cloud.sort_combo.setCurrentIndex(
        cloud.sort_combo.findData(TagCloudWidget.SORT_QUANTITY)
    )
    assert cloud.sort_combo.currentText() == "0-9"
    assert [cloud.sort_combo.itemText(i) for i in range(2)] == ["A-Z", "0-9"]
    assert [tag["tag"] for tag, _chip in cloud._tag_widgets] == [
        "Favorite",
        "Drama",
        "Comedy",
    ]
    font_sizes = {}
    for tag, chip in cloud._tag_widgets:
        tag_button = chip.findChild(QToolButton)
        assert tag_button is not None
        font_sizes[tag["tag"]] = tag_button.font().pointSize()
    assert font_sizes["Favorite"] > font_sizes["Comedy"]
    cloud.filter_edit.setText("dra")
    assert [tag["tag"] for tag, _chip in cloud._tag_widgets] == ["Drama"]

    selected = []
    cloud.tag_selected.connect(
        lambda name, is_selected: selected.append((name, is_selected))
    )
    chip = cloud._tag_widgets[0][1]
    tag_button = chip.findChild(QToolButton)
    assert tag_button is not None
    tag_button.click()
    assert selected == [("Drama", True)]
    assert cloud.selected_tags == ["Drama"]


def test_settings_tags_can_create_tag(qtbot, tmp_path, monkeypatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    for name in (
        "SETTINGS_STATE_FILE",
        "SETTINGS_APP_FILE",
        "SETTINGS_UI_FILE",
        "SETTINGS_MEDIA_FILE",
        "SETTINGS_FILTER_FILE",
    ):
        monkeypatch.setattr(
            f"MyVideoExplorer.settings.settings_state.{name}",
            cfg_dir / f"{name.removeprefix('SETTINGS_').lower()}.json",
        )
    for name in (
        "DEFAULTS_STATE_FILE",
        "DEFAULTS_APP_FILE",
        "DEFAULTS_UI_FILE",
        "DEFAULTS_MEDIA_FILE",
        "DEFAULTS_FILTER_FILE",
    ):
        monkeypatch.setattr(
            f"MyVideoExplorer.settings.settings_state.{name}",
            cfg_dir / "defaults" / f"{name.removeprefix('DEFAULTS_').lower()}.json",
        )
    monkeypatch.setattr("MyVideoExplorer.settings.settings_state.CFG_DIR", cfg_dir)
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_state.PACKAGE_CFG_DIR",
        cfg_dir / "defaults",
    )
    state = SettingsState(MagicMock())
    store = DbTags(state, tmp_path / "tag_catalog.db")
    settings_tab = SettingsTagsTab(state, MagicMock(), store)
    qtbot.addWidget(settings_tab)

    settings_tab.new_tag_edit.setText("NewTag")
    settings_tab.add_tag_button.click()

    assert store.list_tags() == [{"tag": "NewTag", "color": "#808080"}]
    assert settings_tab.save_btn is None
    assert settings_tab.reset_btn is None
    assert any(
        tag["tag"] == "NewTag" for tag in settings_tab.tag_cloud_settings.cloud.tags
    )


def test_tag_name_must_be_alphanumeric(qtbot, tmp_path, monkeypatch):
    """Tags should be alphanumeric only; spaces and punctuation are rejected."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    for name in (
        "SETTINGS_STATE_FILE",
        "SETTINGS_APP_FILE",
        "SETTINGS_UI_FILE",
        "SETTINGS_MEDIA_FILE",
        "SETTINGS_FILTER_FILE",
    ):
        monkeypatch.setattr(
            f"MyVideoExplorer.settings.settings_state.{name}",
            cfg_dir / f"{name.removeprefix('SETTINGS_').lower()}.json",
        )
    for name in (
        "DEFAULTS_STATE_FILE",
        "DEFAULTS_APP_FILE",
        "DEFAULTS_UI_FILE",
        "DEFAULTS_MEDIA_FILE",
        "DEFAULTS_FILTER_FILE",
    ):
        monkeypatch.setattr(
            f"MyVideoExplorer.settings.settings_state.{name}",
            cfg_dir / "defaults" / f"{name.removeprefix('DEFAULTS_').lower()}.json",
        )
    monkeypatch.setattr("MyVideoExplorer.settings.settings_state.CFG_DIR", cfg_dir)
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_state.PACKAGE_CFG_DIR",
        cfg_dir / "defaults",
    )
    state = SettingsState(MagicMock())
    store = DbTags(state, tmp_path / "tag_catalog.db")
    settings_tab = SettingsTagsTab(state, MagicMock(), store)
    qtbot.addWidget(settings_tab)

    # Valid alphanumeric tag should be accepted
    settings_tab.new_tag_edit.setText("Action")
    settings_tab.add_tag_button.click()
    assert store.list_tags() == [{"tag": "Action", "color": "#808080"}]

    # Tag with space should be rejected
    settings_tab.new_tag_edit.setText("Action Comedy")
    settings_tab.add_tag_button.click()
    assert store.list_tags() == [{"tag": "Action", "color": "#808080"}]
    assert settings_tab.new_tag_edit.toolTip() == "Tag names must be alphanumeric only."

    # Tag with punctuation should be rejected
    settings_tab.new_tag_edit.setText("Sci-Fi")
    settings_tab.add_tag_button.click()
    assert store.list_tags() == [{"tag": "Action", "color": "#808080"}]
    assert settings_tab.new_tag_edit.toolTip() == "Tag names must be alphanumeric only."

    # Tag with underscore should be rejected
    settings_tab.new_tag_edit.setText("Sci_Fi")
    settings_tab.add_tag_button.click()
    assert store.list_tags() == [{"tag": "Action", "color": "#808080"}]
    assert settings_tab.new_tag_edit.toolTip() == "Tag names must be alphanumeric only."


def test_normalize_tags_rejects_non_alphanumeric():
    """normalize_tags should filter out tags with spaces or punctuation."""
    result = SettingsState.normalize_tags([
        {"tag": "ValidTag", "color": "#ff0000"},
        {"tag": "Has Space", "color": "#00ff00"},
        {"tag": "Has-Dash", "color": "#0000ff"},
        {"tag": "Has_Underscore", "color": "#ffff00"},
        {"tag": "Has.Dot", "color": "#ff00ff"},
        {"tag": "123", "color": "#00ffff"},
    ])
    tag_names = [item["tag"] for item in result]
    assert "ValidTag" in tag_names
    assert "123" in tag_names
    assert "Has Space" not in tag_names
    assert "Has-Dash" not in tag_names
    assert "Has_Underscore" not in tag_names
    assert "Has.Dot" not in tag_names


def test_is_valid_tag_name():
    """is_valid_tag_name should accept only alphanumeric strings."""
    assert SettingsState.is_valid_tag_name("Action") is True
    assert SettingsState.is_valid_tag_name("123") is True
    assert SettingsState.is_valid_tag_name("Action123") is True
    assert SettingsState.is_valid_tag_name("a") is True
    assert SettingsState.is_valid_tag_name("") is False
    assert SettingsState.is_valid_tag_name("Has Space") is False
    assert SettingsState.is_valid_tag_name("Sci-Fi") is False
    assert SettingsState.is_valid_tag_name("Sci_Fi") is False
    assert SettingsState.is_valid_tag_name("tag!") is False
    assert SettingsState.is_valid_tag_name("tag.") is False
