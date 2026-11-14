from __future__ import annotations


class _UIStrings:
    """Container for all UI strings organized by module."""

    def __init__(self) -> None:
        # --- file_list ---
        self.file_list = _FileListStrings()

        # --- folder_filter ---
        self.folder_filter = _FolderFilterStrings()

        # --- folder_list ---
        self.folder_list = _FolderListStrings()

        # --- image_list ---
        self.image_list = _ImageListStrings()

        # --- media_info ---
        self.media_info = _MediaInfoStrings()

        # --- media_info_side ---
        self.media_info_side = _MediaInfoSideStrings()

        # --- media_info_tabs ---
        self.media_info_tabs = _MediaInfoTabsStrings()

        # --- media_nav_search ---
        self.media_nav_search = _MediaNavSearchStrings()

        # --- filter_criteria_dialog ---
        self.filter_criteria = _FilterCriteriaStrings()
        self.settings = _SettingsStrings()

        # --- widgets ---
        self.widgets = _WidgetStrings()

        # --- compare ---
        self.compare = _CompareStrings()

        # --- tag_cloud ---
        self.tag_cloud = _TagCloudStrings()

        # --- folder_nav ---
        self.folder_nav = _FolderNavStrings()


class _FileListStrings:
    def __init__(self) -> None:
        self.title = "Folder Contents:"
        self.title_with_count = "Folder Contents: ({count})"
        self.tooltip = (
            "File List Usage:\n"
            "- Double-click video to play it\n"
            "- Single-click, selected image will be shown above\n"
            "- Use the scrollbar or mouse wheel to browse files"
        )
        self.tooltip_with_count = (
            "Files in folder: {count}\n\n"
            "File List Usage:\n"
            "- Double-click video to play it\n"
            "- Single-click, selected image will be shown above\n"
            "- Use the scrollbar or mouse wheel to browse files"
        )
        self.open_folder = "Open Folder"
        self.file_type_unknown = "Unknown"
        self.tooltip_item = "Name: {name}\nType: {type}\nPath: {path}"


class _FolderFilterStrings:
    def __init__(self) -> None:
        self.show_all_filter = "- Select a Filter (Showing All) -"
        self.show_all_groups = "- All Groups -"
        self.filter_by_media = "Filter by media folder"
        self.select_filter_group = "Select a filter group"
        self.select_folder = "- Select Folder -"
        self.clear_filter = "Clear Filter"
        self.view_filter_criteria = "View Filter Criteria"
        self.saved_filter_tooltip = "Select a saved filter (type to search)"
        self.default_sort = "Default"
        self.sort_option_labels = {
            "default": "Default",
            "a_z": "A-Z",
            "z_a": "Z-A",
            "last_played": "Last Played",
            "qty_played": "Qty Played",
            "manual": "Manual",
        }
        self.filter_table_placeholder_readonly = "Select a filter from above dropdown"
        self.filter_table_placeholder_edit = "Add a Filter from above"
        self.filter_table_header = ["Filter", "Value"]
        self.filter_table_header_edit = ["Filter", "Value", ""]
        self.add_tag_tooltip = "Add Tag to filter"
        self.remove_tag_tooltip = "Remove tag '{tag}'"
        self.select_tag_placeholder = "- Select Tag -"
        self.select_folder_placeholder = "- Select Folder -"
        self.none_genre = "-none-"
        self.delete_criteria = "Delete Criteria"


class _FolderListStrings:
    def __init__(self) -> None:
        self.title = "Folders"
        self.loading = "Loading..."
        self.empty_state_no_media = "No media folders configured.\nOpen Settings (Gear) → Media and add a media folder."
        self.tooltip = (
            "Folder List Usage:\n"
            "- Click a folder to view its contents\n"
            "- Use 'Add Media Folder' in settings to add more roots\n"
            "- Use the folder picker to browse other directories\n"
            "\n"
            "Settings:\n"
            "- Checking {count} media {plural}\n"
            "- Loading from: {source}"
        )
        self.enqueue_playlist = "Enqueue playlist in default player"
        self.clear_filter_and_search = "Clear Filter and Search"
        self.previous_folder = "Previous folder"
        self.next_folder = "Next folder"
        self.random_folder = "Random folder"
        self.sort_folders = "Sort folders"
        self.sort_default = "Default (A-Z)"
        self.sort_filter = "Filter Sort (Default)"
        self.sort_filter_with_label = "Filter Sort ({label})"
        self.sort_other = "Other"
        self.sort_a_z = "  A-Z"
        self.sort_z_a = "  Z-A"
        self.sort_last_played = "  Last Played"
        self.sort_qty_played = "  Qty Played"


class _ImageListStrings:
    def __init__(self) -> None:
        self.empty_state_no_media = "No media folders configured.\nOpen Settings (Gear) → Media and add a media folder."
        self.empty_state_missing_folder = (
            "This movie folder is missing or inaccessible.\n"
            "Open Settings → Media and rescan your media folders."
        )
        self.no_image_found = (
            "    No image found.\n"
            "    Select a folder by Mouse Wheel over this area\n"
            "    or by Selecting a folder in the Folder list to the left."
        )
        self.loading = "Loading..."
        self.tooltip = (
            "Image Preview Usage:\n"
            "- Use Mouse Wheel to scroll through folders\n"
            "- Double click on image to play media\n"
            "- Right click to scroll through images in current folder"
        )
        self.play_video = "Play Video"
        self.play_with = "Play with {label}"


class _MediaInfoStrings:
    def __init__(self) -> None:
        # Section labels for toolbar buttons
        self.section_common = "Common"
        self.section_plot = "Plot"
        self.section_ids = "IDs"
        self.section_videos = "Videos"
        self.section_audios = "Audios"
        self.section_subtitles = "Subtitles"
        self.section_actors = "Actors"
        self.plot_title = "P\nl\no\nt"


class _MediaInfoSideStrings:
    def __init__(self) -> None:
        self.nfo_title = "NFO"
        self.collapse_nfo = "Collapse NFO column"
        self.expand_nfo = "Expand NFO column"
        self.meta_title = "Meta"
        self.collapse_meta = "Collapse Meta column"
        self.expand_meta = "Expand Meta column"
        self.played = "Played"
        self.last_played = "Last Played"
        self.never_played = "Never"
        self.clear_date = "Clear date"
        self.clear_date_tooltip = "Press Delete or right-click to clear the date."


class _MediaInfoTabsStrings:
    def __init__(self) -> None:
        self.tab_media = "media"
        self.tab_info = "info"
        self.tab_settings = "⚙"
        self.tab_settings_dirty = "⚙*"
        self.settings_tooltip = "Settings"


class _MediaNavSearchStrings:
    def __init__(self) -> None:
        self.search_placeholder = "Search movie name"
        self.search_button = "Search"
        self.search_options = "Search Options"
        self.tags_button = "Tags"
        self.clear_search = "Clear Search"
        self.options_title = "Media Search Options"
        self.movie_name = "Movie name"
        self.folder_name = "Folder name"
        self.file_name = "File name"
        self.actor = "Actor"
        self.director = "Director"
        self.search_person_placeholder = "Search {label}"
        self.year = "Year"
        self.any_year = "- Any -"
        self.qty_played = "Qty Played"
        self.date_last_played = "Date Last Played"
        self.tags_checkbox = "Tags"
        self.select_tags = "Select Tags"
        self.create_filter = "Create Filter from Search"
        self.remove_tag = "Remove tag '{tag}'"
        self.clear_person_criterion = "Clear {label} criterion"
        self.clear_year_criterion = "Clear year criterion"
        self.clear_qty_criterion = "Clear Qty Played criterion"
        self.clear_date_criterion = "Clear Date Last Played criterion"
        self.search_placeholder_dynamic = "Search {field}"


class _FilterCriteriaStrings:
    def __init__(self) -> None:
        self.window_title = "Filter Criteria"
        self.title = "Filter Criteria"
        self.close_tooltip = "Close"
        self.name_label = "Name:"
        self.sort_label = "Sort:"
        self.group_label = "Group:"
        self.visible = "Visible"
        self.default_sort = "Default (use Folder sorting)"
        self.manual_sort = "Manual"
        self.other_live = "Other (live)"
        self.sort_a_z = "A-Z"
        self.sort_z_a = "Z-A"
        self.sort_last_played = "Last Played"
        self.sort_qty_played = "Qty Played"
        self.matched_results = "Matched Results"
        self.folder_video = "Folder / Video"
        self.manual_order = "Manual order"
        self.save_tooltip = "Save"
        self.cancel_tooltip = "Cancel"
        self.delete_filter = "Delete Filter"
        self.edit_filter = "Edit Filter"
        self.criteria_label = "Criteria:"
        self.select_criteria = "- Select a Criteria -"
        self.add_criteria = "Add Criteria"
        self.none_group = "- None -"
        self.invalid_name = "Invalid Filter Name"


class _SettingsStrings:
    def __init__(self) -> None:
        # --- settings_app_tab ---
        self.app = _SettingsAppStrings()

        # --- settings_media_tab ---
        self.media = _SettingsMediaStrings()

        # --- settings_filter_tab ---
        self.filter = _SettingsFilterStrings()

        # --- settings_ui_tab ---
        self.settings_ui = _SettingsUIStrings()

        # --- settings_meta_tab ---
        self.meta = _SettingsMetaStrings()

        # --- settings_player_tab ---
        self.player = _SettingsPlayerStrings()

        # --- settings_tags ---
        self.tags = _SettingsTagsStrings()

        # --- settings_filter_groups_dialog ---
        self.filter_groups = _SettingsFilterGroupsStrings()

        # --- settings_media_folder_browser_section ---
        self.folder_browser = _SettingsFolderBrowserStrings()


class _SettingsAppStrings:
    def __init__(self) -> None:
        self.group_title = "App Settings"
        self.on_app_launch = "On App Launch"
        self.media_group = "Media"
        self.app_group = "App"
        self.auto_select_folder = "Auto select folder"
        self.auto_select_tooltip = "When Folder Nav list refreshes, either select the First Folder, or the Prior Folder"
        self.first_folder = "First Folder"
        self.prior_folder = "Prior Folder"
        self.app_size = "App size"
        self.app_size_tooltip = (
            "Initial size of app window on launch; relative to DPI 100%"
        )
        self.last_window_size = "Last Window Size"
        self.maximized = "Maximized"
        self.app_position = "App position"
        self.app_position_tooltip = "Initial position of app window on launch"
        self.last_position = "Last Position"
        self.center_center = "Center Center"
        self.center_bottom = "Center Bottom"
        self.center_top = "Center Top"
        self.loading_screen = "Loading screen"
        self.hide = "Hide"
        self.show = "Show"
        self.scan_media_timeout = "Scan Media timeout"
        self.scan_media_timeout_tooltip = (
            "Time without scan progress before a media scan is stopped."
        )
        self.nfo_default_state = "NFO default state"
        self.nfo_default_tooltip = (
            "Whether the NFO column starts collapsed or expanded by default"
        )
        self.meta_default_state = "Meta default state"
        self.meta_default_tooltip = (
            "Whether the Meta column starts collapsed or expanded by default"
        )
        self.collapsed = "Collapsed"
        self.expanded = "Expanded"
        self.logging_level = "Logging level"
        self.logging_level_tooltip = "Verbosity of App info logged to log/"
        self.save_btn = "Save App Settings"
        self.reset_btn = "Reset App Settings"


class _SettingsMediaStrings:
    def __init__(self) -> None:
        self.use_local_db = "Use Local DB:"
        self.yes = "Yes"
        self.no = "No"
        self.scan_all = "Scan All"
        self.scan_all_tooltip = "Scan all configured media folders into the database"
        self.media_folders = "Media Folders"
        self.name_header = "Name"
        self.type_header = "Type"
        self.icon_header = "Icon"
        self.reset_btn = "Reset Media Settings"
        self.add_media_folder = "Add Media Folder"
        self.save_btn = "Save Media Settings"
        self.export_tooltip = "Export media settings to JSON"
        self.import_tooltip = "Import media settings from JSON"
        self.export_title = "Export Media Settings"
        self.import_title = "Import Media Settings"
        self.export_complete = "Export Complete"
        self.export_complete_msg = "Media settings exported successfully."
        self.export_failed = "Export Failed"
        self.import_complete = "Import Complete"
        self.import_complete_msg = "Media settings imported successfully."
        self.import_failed = "Import Failed"
        self.db_enabled_tooltip = "Database filtering enabled (Latest update: {date})."
        self.db_disabled_tooltip = (
            "Database filtering disabled. Filtering will be limited."
        )
        self.no_media_folders_msg = (
            "No media folders configured.\nClick the Add Media Folder button below."
        )
        self.scan_all_no_folders = (
            "No configured media folders with valid paths found to scan."
        )
        self.scanning = "Scanning {current} of {total}..."
        self.stopping_stalled = "Stopping stalled scan {current} of {total}..."
        self.confirm_removal = "Confirm removal"
        self.confirm_removal_msg = "Remove Media Folder config\n{label}: {path}?"
        self.invalid_media_settings = "Invalid Media Settings"
        self.media_db_rename_error = "Media DB Rename Error"
        self.new_folder = "New Folder"


class _SettingsFilterStrings:
    def __init__(self) -> None:
        self.group_title = "Filters"
        self.search_label = "Search:"
        self.search_placeholder = "Filter by name..."
        self.refresh_filters = "Refreshing saved filters"
        self.refresh_filters_btn = "Refresh Filters"
        self.refresh_filters_tooltip = "Refresh all saved filters"
        self.add_filter_tooltip = "Add New Filter"
        self.manage_groups_tooltip = "Manage Filter Groups"
        self.export_filters_tooltip = "Export filters to JSON"
        self.import_filters_tooltip = "Import filters from JSON"
        self.criteria_label = "Criteria:"
        self.any_criteria = "- Any Criteria -"
        self.group_label = "Group:"
        self.all_groups = "- All Groups -"
        self.edited_recently = "Edited Recently"
        self.filter_by_tag = "Filter by tag values"
        self.clear_tag_filter = "Clear tag filter"
        self.no_saved_filters = "No saved filters found."
        self.no_match = "No filters match the search criteria."
        self.filter_name_header = "Filter Name"
        self.group_header = "Group"
        self.media_header = "Media"
        self.criteria_header = "Criteria"
        self.edit_filter = "Edit filter '{name}'"
        self.refresh_filter = "Refresh filter '{name}'"
        self.refreshing_filter = "Refreshing filter '{name}'"
        self.delete_filter = "Delete filter '{name}'"
        self.system_filter = "System filter"
        self.manual_needs_refresh = (
            "Manual list needs refresh to rebuild stale entries."
        )
        self.none_group = "(None)"
        self.filter_refresh_failed = "Filter Refresh Failed"
        self.filter_refresh_failed_msg = (
            "Some saved filters could not be refreshed:\n{errors}"
        )
        self.delete_filter_title = "Delete Filter"
        self.delete_filter_msg = "'{name}' matches {count} movies. Delete this filter?"
        self.manual_scan_failed = "Manual Filter Scan Check Failed"
        self.manual_scan_failed_msg = (
            "Manual filter entries could not be checked after the scan:\n{error}"
        )
        self.export_title = "Export Filters"
        self.import_title = "Import Filters"
        self.export_complete = "Export Complete"
        self.export_complete_msg = "Filters exported successfully."
        self.export_failed = "Export Failed"
        self.import_complete = "Import Complete"
        self.import_complete_msg = "Filters imported successfully."
        self.import_failed = "Import Failed"


class _SettingsUIStrings:
    def __init__(self) -> None:
        self.group_title = "UI Settings"
        self.font_size = "Font Size:"
        self.app_font = "App Font"
        self.folder_indentation = "Folder Indentation"
        self.save_btn = "Save UI Settings"
        self.reset_btn = "Reset UI Settings"
        # Indent indicator groups
        self.indent_dots = "Dots"
        self.indent_lines = "Lines"
        self.indent_arrows = "Arrows"
        # Indent indicator options
        self.indent_bullet = "Bullet (•)"
        self.indent_middle_dot = "Middle dot (・)"
        self.indent_period = "Period (.)"
        self.indent_small_square = "Small square (▪)"
        self.indent_hyphen = "Hyphen (-)"
        self.indent_space = "Space"
        self.indent_line_sep = "Line separator (─)"
        self.indent_tree_branch = "Tree branch (├)"
        self.indent_underscore = "Underscore (_)"
        self.indent_vertical_bar = "Vertical bar (│)"
        self.indent_arrow = "Arrow (→)"
        self.indent_left_triangle = "Left triangle (◂)"
        self.indent_right_triangle = "Right triangle (▸)"
        self.indent_right_triangle_small = "Right triangle small (▹)"


class _SettingsMetaStrings:
    def __init__(self) -> None:
        self.ffmpeg_label = "ffmpeg"
        self.download_link = "Download ffmpeg"
        self.browse = "Browse..."
        self.browse_title = "Select ffmpeg Installation Folder"
        self.placeholder = "Select ffmpeg installation folder..."
        self.scan_target = "Scan Target:"
        self.scan_all = "Scan All"
        self.scan_new = "Scan New (only new files)"
        self.scan = "Scan"
        self.scan_tooltip = "Run ffmpeg-based media scan"
        self.stop = "Stop"
        self.stop_tooltip = "Cancel the current scan"
        self.starting_scan = "Starting scan…"
        self.cancelling = "Cancelling…"
        self.ffmpeg_found = "ffmpeg found"
        self.ffmpeg_not_found = "ffmpeg not found"
        self.save_btn = "Save Meta Settings"
        self.reset_btn = "Reset Meta Settings"
        self.scanning = "Scanning {label} ({current} of {total})"
        self.progress = "{current}/{total}: {file}"
        self.error = "Error: {message}"
        self.unable_to_load_stats = "Unable to load scan stats: {error}"
        self.partial_metadata = "({available}/{total} have metadata)"
        self.probed_files = "Probed files"
        self.video_streams = "Video streams"
        self.audio_streams = "Audio streams"
        self.subtitle_streams = "Subtitle streams"
        self.last_probed = "Last probed: {date}"
        self.na = "n/a"


class _SettingsPlayerStrings:
    def __init__(self) -> None:
        self.player_header = "Player"
        self.executable_path = "Executable path"
        self.default_header = "Default"
        self.show_header = "Show"
        self.default_tooltip = (
            "The selected player is used when you double-click a media image."
        )
        self.show_tooltip = (
            "Show this player's play button next to the OS-default play button."
        )
        self.os_default_placeholder = "Provided by the operating system"
        self.executable_placeholder = "Full path to player executable"
        self.arguments_placeholder = (
            "Optional launch arguments (for example: --fullscreen)"
        )
        self.arguments_tooltip = (
            "Arguments are passed to this player before the media file. "
            'Quote values that contain spaces, for example: --profile "My Profile".'
        )
        self.os_default_args_tooltip = (
            "Stored for reference; OS-default playback uses the system file association, "
            "which does not accept custom launch arguments."
        )
        self.browse_tooltip = "Browse for the player's executable."
        self.browse_title = "Select {player_id} executable"
        self.save_btn = "Save Player Settings"
        self.reset_btn = "Reset Player Settings"


class _SettingsTagsStrings:
    def __init__(self) -> None:
        self.export_tooltip = "Export tags to JSON"
        self.import_tooltip = "Import tags from JSON"
        self.export_title = "Export Tags"
        self.import_title = "Import Tags"
        self.export_complete = "Export Complete"
        self.export_complete_msg = "Tags exported successfully."
        self.export_failed = "Export Failed"
        self.import_complete = "Import Complete"
        self.import_complete_msg = "Tags imported successfully."
        self.import_failed = "Import Failed"


class _SettingsFilterGroupsStrings:
    def __init__(self) -> None:
        self.window_title = "Filter Groups"
        self.title = "Filter Groups"
        self.name_header = "Name"
        self.filters_header = "Filters"
        self.no_groups = "No filter groups found."
        self.add_group_tooltip = "Add New Group"
        self.close_tooltip = "Close"
        self.new_group = "New Group:"
        self.enter_group_name = "Enter group name"
        self.create_tooltip = "Create"
        self.cancel_tooltip = "Cancel"
        self.rename_tooltip = "Rename '{name}'"
        self.delete_group_tooltip = "Delete group '{name}'"
        self.system = "system"
        self.invalid_name = "Invalid Name"
        self.invalid_name_msg = "Group name cannot be empty."
        self.create_failed = "Create Failed"
        self.rename_failed = "Rename Failed"
        self.delete_failed = "Delete Failed"
        self.save_tooltip = "Save"


class _SettingsFolderBrowserStrings:
    def __init__(self) -> None:
        self.media_name_placeholder = "Media Name"
        self.media_path_placeholder = "Media Path"
        self.movie = "Movie"
        self.series = "Series"
        self.remove_tooltip = "Remove media folder configuration"
        self.browse_tooltip = "Browse for media folder"
        self.scan = "Scan"
        self.scan_tooltip = "Scan media folder"
        self.stopping = "Stopping..."
        self.stalled = "Stalled for {seconds} seconds; stopping scan"
        self.scan_required = "Scan required"
        self.scan_required_msg = (
            "Please enter both a media name and a media folder before scanning."
        )
        self.invalid_media_name = "Invalid Media Name"
        self.stats_subfolders = "Subfolders"
        self.stats_files = "Files"
        self.stats_images = "Images"
        self.stats_videos = "Videos"
        self.stats_nfo = "NFO Files"
        self.stats_other = "Other Files"
        self.last_scanned = "Last Scanned: {date}"


class _WidgetStrings:
    def __init__(self) -> None:
        self.confirm_deletion = "Confirm deletion"


class _CompareStrings:
    def __init__(self) -> None:
        self.compare_media = "Compare media:"
        self.load_db_first = "Load DB first"
        self.load_db = "Load DB"
        self.local_media = "Local media:"
        self.select_local = "Select local media"
        self.compare = "Compare"
        self.status = "Status:"
        self.search = "Search:"
        self.search_placeholder = "Search all columns..."
        self.previous = "Previous"
        self.next = "Next"
        self.page = "Page {current} / {total}"
        self.import_title = "Import Compare Database"


class _TagCloudStrings:
    def __init__(self) -> None:
        pass


class _FolderNavStrings:
    def __init__(self) -> None:
        pass


class LangEn:
    def __init__(self) -> None:
        self.loading_messages = [
            "Scrolling through the bits..",
            "Calculate calculate..",
            "Shuffling through the 1s and 0s..",
            "Rollin', rollin', rollin'..",
            "Nom nom nom..",
            "Wrangling electrons into place..",
            "Feeding the hamsters in the wheel..",
            "Convincing the pixels to cooperate..",
            "Brewing a fresh batch of data..",
            "Feeding the gremlins..",
            "Polishing each byte by bit..",
            "Herding wild packets across the wire..",
            "Consulting the magic 8-ball..",
            "Teaching the algorithms to sit..",
            "Counting infinity twice to be sure..",
            "Negotiating with the cache goblins..",
            "Loading the unloading loader..",
            "Reversing the polarity of the neutron flow..",
            "Conjuring results from the digital ether..",
            "Spin spin spin..",
            "Spin spun spin..",
        ]
        self.scan_progress = {
            "scanning_media_subfolders": "Scanning Media subfolders",
            "saving_media_data": "Saving Media data",
            "cleaning_old_media_records": "Cleaning old Media rows",
            "preparing_media_rows": "Preparing Media rows",
            "writing_media_rows": "Writing Media rows",
            "saving_media_rows": "Saving Media rows",
            "saved_media_rows": "Saved Media rows",
            "saving_stats": "Saving stats",
            "saved_stats": "Saved stats",
            "done": "Done",
        }
        self.ui = _UIStrings()
