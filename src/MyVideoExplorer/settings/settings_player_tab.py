from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil


class SettingsPlayerTab(SettingsBaseTab):
    """Configure external video-player executable paths and header icons."""

    player_configurations_changed = Signal(object)

    def __init__(
        self, state: SettingsState, log_util: LogUtil, parent: QWidget | None = None
    ) -> None:
        super().__init__(log_util, parent)
        self.state = state
        self._rows: dict[
            str, tuple[QLineEdit, QCheckBox, QRadioButton, QPushButton]
        ] = {}
        self._argument_edits: dict[str, QLineEdit] = {}

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(12)
        self._build_ui()
        self._layout.addStretch()

    def _build_ui(self) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        self._default_group = QButtonGroup(self)
        self._default_group.setExclusive(True)
        for column, title in enumerate(
            ("Player", "Executable path", "Default", "Show")
        ):
            label = QLabel(title, self)
            label.setStyleSheet(APP_THEME.secondary_label_qss())
            if title == "Default":
                label.setToolTip(
                    "The selected player is used when you double-click a media image."
                )
            elif title == "Show":
                label.setToolTip(
                    "Show this player's play button next to the OS-default play button."
                )
            grid.addWidget(label, 0, column)

        for row, config in enumerate(self.state.video_player_configs, start=1):
            player_id = config["id"]
            player_label = QLabel(config["label"], self)
            player_icon = QLabel(self)
            player_icon.setPixmap(
                APP_THEME.icon(
                    self._icon_name(player_id), color=APP_THEME.text_color
                ).pixmap(20, 20)
            )
            player_cell = QWidget(self)
            player_layout = QHBoxLayout(player_cell)
            player_layout.setContentsMargins(0, 0, 0, 0)
            player_layout.setSpacing(8)
            player_layout.addWidget(player_icon)
            player_layout.addWidget(player_label)

            executable_edit = QLineEdit(config["executable"], self)
            executable_edit.setObjectName(f"{player_id}_executable")
            executable_edit.setPlaceholderText(
                "Provided by the operating system"
                if player_id == "os_default"
                else "Full path to player executable"
            )
            browse_button = QPushButton(self)
            browse_button.setObjectName(f"{player_id}_browse_button")
            browse_button.setIcon(
                APP_THEME.icon("fa6s.folder-open", color=APP_THEME.text_color)
            )
            browse_button.setFixedSize(32, 28)
            browse_button.setAccessibleName(f"Browse for {config['label']} executable")
            browse_button.setToolTip("Browse for the player's executable.")
            browse_button.setStyleSheet(APP_THEME.small_button_qss())
            browse_button.clicked.connect(
                lambda checked=False, selected_id=player_id, edit=executable_edit: (
                    self._browse_for_player(selected_id, edit)
                )
            )
            path_cell = QWidget(self)
            path_layout = QVBoxLayout(path_cell)
            path_layout.setContentsMargins(0, 0, 0, 0)
            executable_layout = QHBoxLayout()
            executable_layout.addWidget(executable_edit)
            executable_layout.addWidget(browse_button)
            path_layout.addLayout(executable_layout)
            arguments_edit = QLineEdit(config["arguments"], self)
            arguments_edit.setObjectName(f"{player_id}_arguments")
            arguments_edit.setPlaceholderText(
                "Optional launch arguments (for example: --fullscreen)"
            )
            arguments_edit.setToolTip(
                "Arguments are passed to this player before the media file. "
                'Quote values that contain spaces, for example: --profile "My Profile".'
                if player_id != "os_default"
                else "Stored for reference; OS-default playback uses the system file association, "
                "which does not accept custom launch arguments."
            )
            arguments_edit.textChanged.connect(
                lambda value, config=config: self._update_config(
                    config, "arguments", value
                )
            )
            path_layout.addWidget(arguments_edit)
            self._argument_edits[player_id] = arguments_edit
            show_icon = QCheckBox(self)
            show_icon.setObjectName(f"{player_id}_show_checkbox")
            show_icon.setChecked(config["show_icon"])
            show_icon.setToolTip(
                "Show this player's play button next to the OS-default play button."
            )
            default_radio = QRadioButton(self)
            default_radio.setChecked(config["is_default"])
            default_radio.setToolTip(
                f"Use {config['label']} when you double-click a media image."
            )
            theme_config = APP_THEME.config
            default_radio.setStyleSheet(
                f"""
                QRadioButton::indicator {{
                    width: 14px;
                    height: 14px;
                    border: 2px solid {theme_config.color_border_default};
                    border-radius: 8px;
                    background-color: {theme_config.color_surface_primary};
                }}
                QRadioButton::indicator:checked {{
                    border-color: {theme_config.color_interaction_selected};
                    background-color: {theme_config.color_interaction_selected};
                }}
                """
            )
            self._default_group.addButton(default_radio)
            default_radio.toggled.connect(
                lambda checked, config=config: self._select_default_player(
                    config, checked
                )
            )
            if player_id == "os_default":
                executable_edit.setEnabled(False)
                browse_button.setEnabled(False)
                show_icon.setEnabled(False)
                show_icon.setStyleSheet(
                    f"""
                    QCheckBox:disabled {{ color: {theme_config.color_text_secondary}; }}
                    QCheckBox::indicator:disabled {{
                        background-color: {theme_config.color_surface_disabled};
                        border: 1px solid {theme_config.color_surface_disabled};
                    }}
                    QCheckBox::indicator:checked:disabled {{
                        background-color: {theme_config.color_surface_disabled};
                    }}
                    """
                )
            else:
                executable_edit.textChanged.connect(
                    lambda value, config=config: self._update_config(
                        config, "executable", value
                    )
                )
                show_icon.toggled.connect(
                    lambda checked, config=config: self._update_config(
                        config, "show_icon", checked
                    )
                )

            grid.addWidget(player_cell, row, 0)
            grid.addWidget(path_cell, row, 1)
            grid.addWidget(
                default_radio, row, 2, alignment=Qt.AlignmentFlag.AlignHCenter
            )
            grid.addWidget(show_icon, row, 3, alignment=Qt.AlignmentFlag.AlignHCenter)
            self._rows[player_id] = (
                executable_edit,
                show_icon,
                default_radio,
                browse_button,
            )

        self._layout.addLayout(grid)
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(separator)

        buttons = QWidget(self)
        button_layout = QGridLayout(buttons)
        self.reset_btn = self._build_reset_button(
            "Reset Player Settings", self.reset_settings
        )
        self.save_btn = QPushButton("Save Player Settings", self)
        self.save_btn.clicked.connect(self._save_player_settings)
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        button_layout.addWidget(self.reset_btn, 0, 0)
        button_layout.addWidget(spacer, 0, 1)
        button_layout.addWidget(self.save_btn, 0, 2)
        self._layout.addWidget(buttons)

    def _update_config(self, config: dict[str, Any], key: str, value: Any) -> None:
        if config.get(key) == value:
            return
        config[key] = value
        self.player_configurations_changed.emit(self.state.video_player_configs)
        self._on_setting_changed()

    def _select_default_player(
        self, selected_config: dict[str, Any], checked: bool
    ) -> None:
        if not checked:
            return
        changed = False
        for config in self.state.video_player_configs:
            is_default = config is selected_config
            if config["is_default"] != is_default:
                config["is_default"] = is_default
                changed = True
        if changed:
            self.player_configurations_changed.emit(self.state.video_player_configs)
            self._on_setting_changed()

    def _browse_for_player(self, player_id: str, executable_edit: QLineEdit) -> None:
        executable, _ = QFileDialog.getOpenFileName(
            self, f"Select {player_id} executable", executable_edit.text()
        )
        if executable:
            executable_edit.setText(executable)

    def reset_settings(self) -> None:
        self.state.load_player()
        for config in self.state.video_player_configs:
            executable_edit, show_icon, default_radio, _ = self._rows[config["id"]]
            executable_edit.blockSignals(True)
            show_icon.blockSignals(True)
            default_radio.blockSignals(True)
            executable_edit.setText(config["executable"])
            show_icon.setChecked(config["show_icon"])
            default_radio.setChecked(config["is_default"])
            arguments_edit = self._argument_edits.get(config["id"])
            if arguments_edit is not None:
                arguments_edit.blockSignals(True)
                arguments_edit.setText(config["arguments"])
                arguments_edit.blockSignals(False)
            executable_edit.blockSignals(False)
            show_icon.blockSignals(False)
            default_radio.blockSignals(False)
        self.player_configurations_changed.emit(self.state.video_player_configs)
        self.reset_save_button()

    def _save_player_settings(self) -> None:
        self.state.save_player()
        self.reset_save_button()
        self.saved.emit(None)

    @staticmethod
    def _icon_name(player_id: str) -> str:
        return {
            "os_default": "fa6s.circle-play",
            "vlc": "fa6s.play",
            "potplayer": "fa6s.film",
            "mpc_qt": "fa6s.clapperboard",
            "custom": "fa6s.video",
        }[player_id]
