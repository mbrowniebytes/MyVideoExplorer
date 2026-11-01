from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.buttons.delayed_delete_button import DelayedDeleteButton


def test_action_button_sets_icon_tooltip_and_background_matched_border(qtbot):
    button = ActionButton(
        icon_name="fa6s.magnifying-glass",
        tooltip="Search",
    )
    qtbot.addWidget(button)

    style = button.styleSheet()
    surface = APP_THEME.config.color_surface_primary
    assert not button.icon().isNull()
    assert button.toolTip() == "Search"
    assert f"border: 1px solid {surface};" in style
    APP_THEME.setup_button(button)
    assert f"border: 1px solid {surface};" in button.styleSheet()


def test_delayed_delete_button_is_an_action_button(qtbot):
    button = DelayedDeleteButton(unlock_delay_ms=0)
    qtbot.addWidget(button)

    assert isinstance(button, ActionButton)
