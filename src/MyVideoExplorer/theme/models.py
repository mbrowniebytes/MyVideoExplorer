from dataclasses import dataclass

@dataclass
class ThemeConfig:
    """Holds all raw values for the application theme."""

    # Typography
    # "Segoe UI" default windows
    # "Source Sans Pro" "Montserrat" "Lato" "Nunito"
    # "Righteous" "SyneMono"
    font_family_default: str = "Lato, Segoe UI"
    font_size_base: int = 18

    # Color Palette - Backgrounds
    color_background_main: str = "#111111"
    color_background_gradient: str = "#131613"
    color_surface_primary: str = "rgba(59, 89, 99, 99)"
    color_surface_alternate: str = "#151B21"
    color_surface_disabled: str = "rgba(128, 128, 128, 128)"

    # Color Palette - Text
    color_text_primary: str = "#E6EDF3"
    color_text_muted: str = "#AAB4C0"
    color_text_secondary: str = "#A6ADB3"
    color_text_field_value: str = "#E6EDF3"

    # UI Interaction & Borders
    color_border_default: str = "rgba(150, 202, 214, 140)"
    color_border_highlight: str = "rgba(20, 232, 244, 140)"
    color_border_icon: str = "rgba(111, 111, 111, 200)"
    color_interaction_hover: str = "rgba(59, 130, 246, 25)"
    color_interaction_pressed: str = "rgba(59, 130, 246, 40)"
    color_interaction_selected: str = "#2B6296"
    color_interaction_selected_text: str = "#FFFFFF"

    # Highlight QPixmap inside QLabel
    color_interaction_pixmap: str = "#1B6166AA"
    size_interaction_pixmap: int = 20

    # Scrollbar & Splitters
    color_scrollbar_background: str = "#1E1E1E"
    color_scrollbar_handle: str = "#4F4F5F"
    color_scrollbar_handle_hover: str = "#5E5E7E"
    color_splitter_handle: str = "#4B4246"
    size_splitter_handle_width: int = 1

    # Structure & Layout
    color_section_divider: str = "#4B4246"
    size_border_radius_standard: int = 8

    # List Item Padding
    padding_list_item_vertical: int = 4
    padding_list_item_horizontal: int = 10
    margin_list_item_vertical: int = 0
    margin_list_item_horizontal: int = 2

    # Button Metrics
    padding_button_small_v: int = 3
    padding_button_small_h: int = 6
    padding_button_standard_v: int = 6
    padding_button_standard_h: int = 8
    size_button_minimum_height: int = 48
    size_standard_icon: int = 20
