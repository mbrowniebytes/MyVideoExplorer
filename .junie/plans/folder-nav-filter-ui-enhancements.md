---
sessionId: session-261030-195826-9b4o
---

# Requirements

### Overview & Goals
Enhance the folder navigation UI with four improvements to filter and search interactions: add Edit/Create Filter buttons, reposition the Tags button, and make Clear Filter clear both filter and search criteria.

### Scope

**In Scope:**
1. **Filter Criteria → Edit button**: Add a fa6s.pen-to-square Edit button to the bottom-right of the Filter Criteria popup in `FolderFilters`. When clicked, switch the right pane to Settings → Filters and open the edit dialog for the currently selected filter.
2. **Tags button moved down**: In `FolderFilters`, move the Tags button from the saved filters row to a new row below, positioned to the right of the Search Options button in `MediaNavSearchWidget`.
3. **Clear Filter clears both**: The Clear Filter button in `FolderListHeader` should clear both the saved filter selection AND the quick search criteria (text + options).
4. **Quick search → Create Filter button**: In `MediaNavSearchWidget`, when quick search criteria chips are visible, add a fa6s.circle-plus Create Filter button at the bottom-right. When clicked, switch to Settings → Filters and open a new filter dialog.

**Out of Scope:**
- Changes to filter logic or database queries.
- Modifications to the Settings → Filters tab's internal layout beyond exposing public methods.
- Any changes to video playback or media info panels.

### User Stories
- As a user, I want to edit a saved filter directly from the Filter Criteria popup so I don't have to navigate to Settings manually.
- As a user, I want the Tags button near the search controls so the layout is more intuitive.
- As a user, I want the Clear Filter button to clear both my filter and search criteria so I get a clean slate in one click.
- As a user, I want to create a filter from my current quick search criteria so I can save my search as a reusable filter.

### Functional Requirements
1. **Edit Filter button**: The Filter Criteria readonly popup gains an Edit button (fa6s.pen-to-square) at bottom-right. Clicking emits `edit_filter_requested` signal with the current filter name.
2. **Tags button repositioned**: Remove `tag_button` from `saved_filters_layout` in `FolderFilters.build()`. Add it to a new row in `MediaNavSearchWidget` next to the Search Options button.
3. **Clear Filter clears both**: When `clear_filter_requested` is emitted, it should also trigger `media_nav_search.clear_search()` to clear search text and options.
4. **Create Filter button**: When `criteria_summary` chips are visible in `MediaNavSearchWidget`, show a Create Filter button (fa6s.circle-plus) at bottom-right. Clicking emits `create_filter_requested` signal.

# Technical Design

### Current Implementation

- **FolderFilters** (`src/MyVideoExplorer/folder_filter/folder_filter.py`): Builds the left-pane filter UI. The `_show_filter_criteria()` method creates a readonly `FilterCriteriaDialog` popup. The `saved_filters_layout` row contains: `saved_filters_combo`, `filter_criteria_button`, `tag_button`, `apply_button`.
- **MediaNavSearchWidget** (`src/MyVideoExplorer/folder_list/media_nav_search_widget.py`): Quick search widget with search box, Search button, Search Options button, and Clear button. Shows criteria chips in `criteria_summary`.
- **FolderListHeader** (`src/MyVideoExplorer/folder_list/folder_list_header.py`): Contains the Clear Filter button that emits `clear_filter_clicked`.
- **FolderList** (`src/MyVideoExplorer/folder_list/folder_list.py`): Wires `clear_filter_clicked` → `clear_filter_requested` signal. Has access to `media_nav_search`.
- **AppContainer** (`src/MyVideoExplorer/app/app_container.py`): Composition root that wires all signals.
- **SettingsFilterTab** (`src/MyVideoExplorer/settings/settings_filter_tab.py`): Has `_open_edit_dialog(filter_cfg)` and `_on_add_filter()` methods (both private).
- **MediaInfoTabs** (`src/MyVideoExplorer/media_info_tabs/media_info_tabs.py`): Has `show_settings_tab()` to switch to Settings.
- **Settings** (`src/MyVideoExplorer/settings/settings.py`): Has `settings_tabs_container` (QTabWidget) with Filters at index 4.

### Key Decisions
- **Signal-based communication**: Components emit signals (`edit_filter_requested`, `create_filter_requested`); AppContainer wires them. This keeps UI widgets decoupled.
- **Expose public methods on SettingsFilterTab**: Rename `_open_edit_dialog` → `open_edit_dialog` and `_on_add_filter` → `open_add_filter`.
- **Tags button lives in MediaNavSearchWidget**: Moved to a new row near the Search Options button.

### Proposed Changes

#### 1. FolderFilters — Edit Filter signal + remove Tags button
**File**: `src/MyVideoExplorer/folder_filter/folder_filter.py`
- Add signal `edit_filter_requested = Signal(str)`.
- In `_build_filter_criteria_popup()`, add an Edit button (fa6s.pen-to-square) to the dialog's button layout. On click, emit `edit_filter_requested` with the current filter name.
- Remove `tag_button` from `saved_filters_layout` in `build()` and remove `_build_tag_button()`.

#### 2. MediaNavSearchWidget — Create Filter + Tags button
**File**: `src/MyVideoExplorer/folder_list/media_nav_search_widget.py`
- Add signal `create_filter_requested = Signal()`.
- Add a Create Filter button (fa6s.circle-plus) visible when criteria chips are shown.
- Add the Tags button (fa6s.tag) to the main row, next to Search Options.
- Wire Tags button to show tag picker dialog.
- On Create Filter click, emit `create_filter_requested`.

#### 3. Clear Filter clears both
**File**: `src/MyVideoExplorer/folder_list/folder_list.py`
- Update the `clear_filter_clicked` handler to also call `self.media_nav_search.clear_search()`.

#### 4. SettingsFilterTab — expose public methods
**File**: `src/MyVideoExplorer/settings/settings_filter_tab.py`
- Rename `_open_edit_dialog` to `open_edit_dialog`.
- Rename `_on_add_filter` to `open_add_filter`.

#### 5. AppContainer — wire new signals
**File**: `src/MyVideoExplorer/app/app_container.py`
- Wire `folder_nav_filters.edit_filter_requested` to switch to Settings → Filters and open edit dialog.
- Wire `folder_list.media_nav_search.create_filter_requested` to switch to Settings → Filters and open add dialog.

### Architecture Diagram

``` mermaid
graph LR
  A[FolderFilters] -->|edit_filter_requested| B[AppContainer]
  C[MediaNavSearchWidget] -->|create_filter_requested| B
  D[FolderListHeader] -->|clear_filter_clicked| E[FolderList]
  E -->|clear_search| C
  B -->|show_settings + open_edit| F[SettingsFilterTab]
  B -->|show_settings + open_add| F
```

### File Structure

**Modified files:**
- `src/MyVideoExplorer/folder_filter/folder_filter.py`
- `src/MyVideoExplorer/folder_list/media_nav_search_widget.py`
- `src/MyVideoExplorer/folder_list/folder_list.py`
- `src/MyVideoExplorer/settings/settings_filter_tab.py`
- `src/MyVideoExplorer/app/app_container.py`

# Testing

### Key Scenarios
1. **Edit Filter from popup**: Select a saved filter → click Filter Criteria → click Edit → right pane switches to Settings → Filters → edit dialog opens pre-filled.
2. **Tags button position**: Tags button appears in the search widget row, next to Search Options.
3. **Clear Filter clears both**: Set a filter and search text → click Clear Filter → both reset.
4. **Create Filter from quick search**: Set search criteria → Create Filter button visible → click → Settings → Filters → new filter dialog opens.

### Edge Cases
- Edit Filter when no filter selected (index 0): Edit button disabled or no-op.
- Create Filter when no criteria active: Button hidden.
- Clear Filter when no filter active: Still clears search if present.

# Delivery Steps

### ✓ Step 1: Expose SettingsFilterTab public methods
Make `open_edit_dialog` and `open_add_filter` public in SettingsFilterTab.
- Rename `_open_edit_dialog` to `open_edit_dialog` in `settings_filter_tab.py`.
- Rename `_on_add_filter` to `open_add_filter` in `settings_filter_tab.py`.
- Update internal call sites to use the new names.

### ✓ Step 2: Add Edit Filter button to popup and remove Tags from FolderFilters
FolderFilters gains an `edit_filter_requested` signal; Tags button is removed.
- Add `edit_filter_requested = Signal(str)` to `FolderFilters`.
- In `_build_filter_criteria_popup()`, add an Edit button (fa6s.pen-to-square); on click, emit `edit_filter_requested` with the current filter name.
- Remove `tag_button` from `saved_filters_layout` and `_build_tag_button()` from `build()`.

### ✓ Step 3: Add Create Filter and Tags buttons to MediaNavSearchWidget
MediaNavSearchWidget gains a Create Filter button and the Tags button.
- Add `create_filter_requested = Signal()` to `MediaNavSearchWidget`.
- Add a Create Filter button (fa6s.circle-plus) visible when criteria chips are shown.
- Add the Tags button (fa6s.tag) to the main row, next to Search Options.
- Wire Tags button to show tag picker dialog.
- Update `_refresh_criteria_summary` to show/hide Create Filter button.

### ✓ Step 4: Clear Filter clears both filter and search
FolderList clears search when Clear Filter is clicked.
- In `folder_list.py`, update the `clear_filter_clicked` handler to also call `self.media_nav_search.clear_search()`.

### ✓ Step 5: Wire new signals in AppContainer
AppContainer connects the new signals to the Settings → Filters workflow.
- Wire `folder_nav_filters.edit_filter_requested` to switch to Settings → Filters and open the edit dialog.
- Wire `folder_list.media_nav_search.create_filter_requested` to switch to Settings → Filters and open the add filter dialog.
- Both handlers call `media_info_tabs.show_settings_tab()`, switch to Filters tab (index 4), then call the appropriate method on `settings.filter_settings_tab`.

---
## Phase 2: Follow-up UI refinements

### Overview & Goals
Three follow-up UI improvements: make filter list columns sortable, move Create Filter into Search Options dialog, and move Edit Filter natively into FilterCriteriaDialog.

### ✓ Step 6: Add sortable Name and Count columns to Settings Filter list
SettingsFilterTab filter table gains clickable column headers for Name and Count sorting.
- In `settings_filter_tab.py`, enable sorting on the QTableWidget header for COL_NAME and COL_COUNT columns.
- Make the header sortable by calling `header.setSortIndicatorShown(True)` and connecting `header.sortIndicatorChanged` to re-sort the filtered list.
- Store the current sort column and order, apply sorting in `_refresh_filter_list` before populating rows.
- Default sort: Name ascending.

### ✓ Step 7: Move Create Filter button from Search widget to Search Options dialog
Move the Create Filter button from MediaNavSearchWidget into MediaNavSearchOptionsDialog.
- Remove `create_filter_button` from `MediaNavSearchWidget` layout and related code.
- Add a Create Filter button (fa6s.circle-plus) to the bottom-right of `MediaNavSearchOptionsDialog`.
- Wire the button to emit `create_filter_requested` from `MediaNavSearchWidget` via the dialog's `criteria_changed` signal or a new signal.
- Remove `create_filter_requested` signal from `MediaNavSearchWidget` if no longer needed there, or keep it and wire from the dialog.

### ✓ Step 8: Move Edit Filter button natively into FilterCriteriaDialog
Move the Edit Filter button from FolderFilters' `_add_edit_button_to_popup` into FilterCriteriaDialog itself.
- Add an optional `edit_requested = Signal(str)` signal to `FilterCriteriaDialog`.
- In `_build_ui`, when in readonly mode, add an Edit button (fa6s.pen-to-square) at bottom-right of the button layout.
- Remove `_add_edit_button_to_popup` from `FolderFilters` since the dialog now handles it natively.
- Wire `edit_requested` in `FolderFilters._build_filter_criteria_popup` to emit `edit_filter_requested`.

---
## Phase 3: Create Filter from Search & Edit Filter Enable

### Overview & Goals
Two follow-up improvements: copy current search criteria to the new filter dialog when clicking Create Filter, and enable the Edit Filter button in FilterCriteriaDialog readonly mode.

### ✓ Step 9: Copy search criteria to new filter dialog
When clicking Create Filter in Search Options dialog, collect the current search criteria and pass them to the new filter dialog.
- In `MediaNavSearchOptionsDialog`, add a method `collect_criteria_as_filters()` that returns a list of filter dicts matching the current search state.
- Map search fields to filter types: movie_name/folder_name/file_name → Title/Folder/File, actor/director → Actor/Director, tags → Tag, qty_played → Qty Played, last_played → Last Played, year → Title (with year value).
- Update `create_filter_requested` signal to carry the collected filters: `create_filter_requested = Signal(list)`.
- In `AppContainer._on_create_filter_requested`, pass the filters to `open_add_filter`.
- In `SettingsFilterTab.open_add_filter`, accept an optional filters parameter and pre-fill the dialog.

### ✓ Step 10: Enable Edit Filter button in readonly mode
Remove the disabled state check so the Edit Filter button is always enabled in FilterCriteriaDialog readonly mode.
- In `filter_criteria_dialog.py`, remove the `if not self._filter_name: edit_btn.setEnabled(False)` check.
- The Edit button should be enabled even when no filter name is present, allowing the user to start editing from an empty state.