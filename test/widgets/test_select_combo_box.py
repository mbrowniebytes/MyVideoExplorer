from MyVideoExplorer.theme.style.style_combo import StyleCombo
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox


def test_select_combo_box_uses_application_theme(qtbot):
    combo = SelectComboBox()
    qtbot.addWidget(combo)
    combo.addItem("Folder", "folder-path")

    assert combo.currentData() == "folder-path"
    assert combo.styleSheet() == StyleCombo.get_combo_qss(APP_THEME.config)
