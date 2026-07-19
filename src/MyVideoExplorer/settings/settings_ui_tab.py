from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.settings.settings import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil


class SettingsUITab(SettingsBaseTab):
    def __init__(
        self,
            state: SettingsState,
            log_util: LogUtil,
            file_util: FileUtil,
            parent: QWidget | None = None
    ) -> None:
        super().__init__(log_util, parent)
        self.file_util = file_util
        self.state = state

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.main_widget = QWidget()
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(15)

        self._build_ui()
        self.content_layout.addStretch()

        scroll.setWidget(self.main_widget)
        self.layout.addWidget(scroll)

    def _build_ui(self) -> None:
        display_group = QGroupBox("UI Settings")
        display_layout = QFormLayout(display_group)

        # Font size
        self.font_size_combo = QComboBox()
        current_index = 0
        for index, font_size in enumerate(range(15, 26)):
            if font_size == APP_THEME.font_size:
                current_index = index
            self.font_size_combo.addItem(str(font_size), font_size)
        self.font_size_combo.setCurrentIndex(current_index)

        self.font_size_combo.currentIndexChanged.connect(self._on_font_size_changed)
        self.font_size_combo.currentIndexChanged.connect(self._on_setting_changed)

        display_layout.addRow("Font Size:", self.font_size_combo)

        # App Font
        self.font_family_combo = QComboBox()

        path_to_fonts = self.file_util.get_resource_path("asset/fonts")
        fonts_dir = Path(path_to_fonts)

        ttf_fonts = list(fonts_dir.glob("*.ttf"))

        current_font = APP_THEME.font_family
        main_current_family = current_font.split(",")[0].strip()

        current_index = -1
        for font_file in ttf_fonts:
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id == -1:
                continue
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                family = families[0]
                self.font_family_combo.addItem(family, font_file.name)

                # Style each item with its own font for preview
                index = self.font_family_combo.count() - 1
                item_font = QFont(family, 12)
                self.font_family_combo.setItemData(
                    index, item_font, Qt.ItemDataRole.FontRole
                )

                if family == main_current_family:
                    current_index = self.font_family_combo.count() - 1

        if current_index != -1:
            self.font_family_combo.setCurrentIndex(current_index)

        self.font_family_combo.currentIndexChanged.connect(self._on_font_family_changed)
        # self.font_family_combo.currentIndexChanged.connect(self._on_setting_changed)

        display_layout.addRow("App Font", self.font_family_combo)

        self.content_layout.addWidget(display_group)

        # Add stretch to push save button to bottom even when content is short
        self.content_layout.addStretch(2)

        # Move Save UI Settings button to bottom-right, centered
        save_btn_container = QWidget()
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save UI Settings")
        self.save_btn.clicked.connect(self._save_ui_settings)

        self.reset_btn = self._build_reset_button(
            "Reset UI Settings", self.reset_settings
        )

        spacer = QWidget()
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        save_btn_layout.addWidget(self.reset_btn)
        save_btn_layout.addWidget(spacer)
        save_btn_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(
            save_btn_container,
            # alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
            alignment=Qt.AlignmentFlag.AlignBottom,
        )

    def reset_settings(self) -> None:
        """Reset settings for this tab."""
        self.state.load_ui()

        # Update font size combo
        for i in range(self.font_size_combo.count()):
            if self.font_size_combo.itemData(i) == APP_THEME.font_size:
                self.font_size_combo.setCurrentIndex(i)
                break

        # Update font family combo
        main_current_family = APP_THEME.font_family.split(",")[0].strip()
        for i in range(self.font_family_combo.count()):
            if self.font_family_combo.itemText(i) == main_current_family:
                self.font_family_combo.setCurrentIndex(i)
                break

        APP_THEME.refresh_theme()
        self.reset_save_button()
        self.sig_saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="UI Settings Reset",
                description="UI settings were reset to defaults.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("UI Settings reset")

    def _on_font_size_changed(self, index: int) -> None:
        value = self.font_size_combo.itemData(index, role=Qt.ItemDataRole.UserRole)
        if not value:
            return
        if value == APP_THEME.font_size:
            return
        if value < 15 or value > 25:
            return

        print(f"_on_font_size_changed: index:{index} value:{value}")
        APP_THEME.font_size = value
        # Block signals on spinbox before refresh_theme to prevent re-triggering during apply_theme
        self.font_size_combo.blockSignals(True)
        try:
            APP_THEME.refresh_theme()
        finally:
            self.font_size_combo.blockSignals(False)

        self.state.sig_settings_changed.emit(
            SignalPayload(
                data=value,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Font size was changed.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        self._on_setting_changed()

    def _on_font_family_changed(self, index: int) -> None:
        family = self.font_family_combo.itemText(index)
        if not family:
            return
        if family == APP_THEME.font_family:
            return

        # print(f"_on_font_family_changed: index:{index} family:{family}")
        APP_THEME.font_family = family
        # Block signals on combo before refresh_theme to prevent re-triggering during apply_theme
        self.font_family_combo.blockSignals(True)
        try:
            APP_THEME.refresh_theme()
        finally:
            self.font_family_combo.blockSignals(False)

        # self.state.sig_settings_changed.emit(
        #     SignalPayload(
        #         data=family,
        #         sender=self.__class__.__name__,
        #         name="Settings Changed",
        #         description="Font family was changed.",
        #         flow=SignalFlow.USER_INPUT,
        #     )
        # )
        self._on_setting_changed()

    def _save_ui_settings(self) -> None:
        """Save only UI tab settings."""
        self.state.save_ui()
        self.reset_save_button()
        self.sig_saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="UI Settings Saved",
                description="UI settings were saved.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("UI Settings saved")

    def apply_theme(self) -> None:
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)

        self.main_widget.setFont(font)
