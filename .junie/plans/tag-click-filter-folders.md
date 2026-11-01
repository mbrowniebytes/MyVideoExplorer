---
sessionId: session-261030-215020-88sv
---

# Requirements

### Overview & Goals
When a user clicks a tag in either the **Media list** (info side panel) or the **Settings Tags** panel, the app should:
1. Clear the current folder filter and media search
2. Add the clicked tag to the media search box tags
3. Re-filter the folder list by that tag

### User Stories
- As a user, when I click a tag in the media info side panel, I want the folder list to filter to folders containing that tag, so I can quickly browse all media with that tag.
- As a user, when I click a tag in the Settings → Tags panel, I want the same behavior — clear current filters, add the tag to the search, and filter the folder list.

### Functional Requirements
1. **Media list tags (`TagCloudMedia`)**: Clicking an assigned tag button in the media info side panel should emit a signal that triggers the filter-and-search flow.
2. **Settings tags (`TagCloudSettings` / `TagCloudWidget`)**: Clicking a tag chip in the settings tags cloud should emit a signal that triggers the same flow.
3. **Clear current state**: Before applying the tag filter, clear any active saved filter and clear the media search box (text + selected tags).
4. **Add tag to media search box**: The clicked tag should appear as a selected tag chip in the `MediaNavSearchWidget`.
5. **Filter folder list**: The `FolderFilters` should include the tag in its filter criteria and re-apply filtering.

### Scope
- **In Scope**: `TagCloudMedia` (media info side panel), `TagCloudSettings` (settings tags tab), `FolderFilters`, `MediaNavSearchWidget`, `FolderNav`, and `AppContainer` signal wiring.
- **Out of Scope**: Changes to tag creation, editing, or deletion. Changes to the tag picker dialog. Changes to the media search options dialog beyond adding tags.

# Technical Design

### Current Implementation
- **`TagCloudMedia`** (`tag_cloud/tag_cloud_media.py`): Renders assigned tags for the current media file as `TagButton` widgets in `_render_assigned_tags()`. These buttons have **no click handler** — clicking does nothing. The widget emits `tag_added`/`tag_removed` signals when tags are added/removed via the tag picker dialog.
- **`TagCloudSettings`** (`tag_cloud/tag_cloud_settings.py`): Uses `TagCloudWidget` which emits `tag_selected(tag_name, checked)` on click, but this signal is **not wired** to anything.
- **`FolderFilters`** (`folder_filter/folder_filter.py`): Already has `add_selected_tag(tag)`, `clear_selected_tags()`, `clear_saved_filter()`, and `apply_filters()` methods. Tags added via `add_selected_tag` are included in filter criteria as `{"filter": "Tag", "value": tag}`.
- **`MediaNavSearchWidget`** (`folder_list/media_nav_search_widget.py`): Already has `add_selected_tag(tag)` method that adds tags to the search criteria.
- **`FolderNav`** (`folder_nav/folder_nav.py`): Has `clear_saved_filter()` which clears the saved filter combo and re-applies filters.
- **`AppContainer`** (`app/app_container.py`): Central DI and signal wiring hub. Already wires `tag_cloud_widget.tag_added` → `_add_media_tag` and `tag_removed` → `_remove_media_tag` in `media_info_side_view`.

### Key Decisions
- **Emit a new signal from `TagCloudMedia`** when an assigned tag button is clicked, rather than handling the click inline. This keeps the widget self-contained and follows the existing decoupling pattern (communicate via signals).
- **Wire both tag sources through `AppContainer`** to a single handler method that clears filters, adds the tag, and re-filters. This avoids code duplication and keeps the cross-module coordination in one place.
- **Use existing `FolderFilters.add_selected_tag()` and `MediaNavSearchWidget.add_selected_tag()`** rather than duplicating tag management logic.

### Proposed Changes

#### 1. `TagCloudMedia` — emit `tag_clicked` signal on assigned tag button click
- Add a new signal `tag_clicked = Signal(str)` to `TagCloudMedia`.
- In `_render_assigned_tags()`, connect each `TagButton.clicked` to emit `tag_clicked(tag)`.

#### 2. `TagCloudSettings` — wire `tag_selected` to a new `tag_clicked` signal
- Add a new signal `tag_clicked = Signal(str)` to `TagCloudSettings`.
- In `__init__`, connect `self.cloud.tag_selected` to emit `tag_clicked` when `checked=True` (single click toggles check; we only want the "select" direction).

#### 3. `AppContainer` — wire both tag click signals to a shared handler
- Connect `media_info_side_view.tag_cloud_widget.tag_clicked` → new `_on_tag_clicked_for_filter(tag)` method.
- Connect `settings.tags_settings_tab.tag_cloud_settings.tag_clicked` → same `_on_tag_clicked_for_filter(tag)` method.
- `_on_tag_clicked_for_filter(tag)` should:
  1. Clear the saved filter: `folder_nav.clear_saved_filter()`
  2. Clear the media search box text: `folder_list.media_nav_search_box.clear()`
  3. Clear existing selected tags in media search: `folder_list.media_nav_search.remove_selected_tag` for each, then clear.
  4. Add the clicked tag to `folder_nav_filters.selected_tags` via `add_selected_tag(tag)`.
  5. Add the clicked tag to `folder_list.media_nav_search` via `add_selected_tag(tag)`.
  6. Re-apply filters: `folder_nav.apply_filters()`.

### Architecture Diagram

``` mermaid
graph LR
  A[TagCloudMedia\nassigned tag click] -->|tag_clicked| C[AppContainer]
  B[TagCloudSettings\ntag chip click] -->|tag_clicked| C
  C -->|clear_saved_filter| D[FolderNav]
  C -->|clear search| E[MediaNavSearchWidget]
  C -->|add_selected_tag| F[FolderFilters]
  C -->|add_selected_tag| E
  C -->|apply_filters| D
  D -->|filtered items| G[FolderList]
```

### Files Modified
- `src/MyVideoExplorer/tag_cloud/tag_cloud_media.py` — add `tag_clicked` signal, wire in `_render_assigned_tags`
- `src/MyVideoExplorer/tag_cloud/tag_cloud_settings.py` — add `tag_clicked` signal, wire `cloud.tag_selected`
- `src/MyVideoExplorer/app/app_container.py` — wire both signals to `_on_tag_clicked_for_filter`

# Delivery Steps

### ✓ Step 1: Add tag_clicked signal to TagCloudMedia
Make assigned tag buttons in the media info side panel emit a signal when clicked.
- Add `tag_clicked = Signal(str)` to `TagCloudMedia` class.
- In `_render_assigned_tags()`, connect each `TagButton.clicked` to emit `tag_clicked(tag)` via a lambda closure.
- This keeps the widget self-contained and follows the existing signal-based decoupling pattern.

### ✓ Step 2: Add tag_clicked signal to TagCloudSettings
Make tag chips in the settings tags panel emit a signal when clicked.
- Add `tag_clicked = Signal(str)` to `TagCloudSettings` class.
- In `__init__`, connect `self.cloud.tag_selected` to a handler that emits `tag_clicked(tag_name)` only when `checked=True` (i.e., the tag was selected, not deselected).
- This bridges the `TagCloudWidget.tag_selected(tag, bool)` signal to a simpler single-argument signal.

### ✓ Step 3: Wire tag clicks in AppContainer to clear filter, add tag, and re-filter
Connect both tag click sources to a shared handler that performs the full filter-and-search flow.
- Add `_on_tag_clicked_for_filter(tag)` method to `AppContainer`.
- The method will:
  - Call `folder_nav.clear_saved_filter()` to clear any active saved filter.
  - Clear `folder_list.media_nav_search_box` text.
  - Clear existing selected tags in `folder_list.media_nav_search` and `folder_nav_filters`.
  - Add the clicked tag to `folder_nav_filters` via `add_selected_tag(tag)`.
  - Add the clicked tag to `folder_list.media_nav_search` via `add_selected_tag(tag)`.
  - Call `folder_nav.apply_filters()` to re-filter the folder list.
- Wire `media_info_side_view.tag_cloud_widget.tag_clicked` → `_on_tag_clicked_for_filter`.
- Wire `settings.tags_settings_tab.tag_cloud_settings.tag_clicked` → `_on_tag_clicked_for_filter`.
- Run `ruff check --fix` and `ruff format` to ensure lint/format compliance.

### ✓ Step 4: Add "Search" button to Settings Tags cloud
Add a "Search" button next to each tag chip in the Settings Tags panel that adds the tag to the media search criteria without clearing filters or re-filtering folders.
- Add `search_button_enabled = True` option to `TagCloudWidget.__init__` and `_make_chip()`.
- When enabled, add a small search icon button (magnifying glass) next to each tag chip's label.
- Emit a new signal `tag_search_requested = Signal(str)` from `TagCloudWidget` when the search button is clicked.
- Bridge this signal through `TagCloudSettings` as `tag_search_requested = Signal(str)`.
- Wire in `AppContainer`: `settings.tags_settings_tab.tag_cloud_settings.tag_search_requested` → new `_on_tag_search_requested(tag)` that only adds the tag to `folder_list.media_nav_search` via `add_selected_tag(tag)` (no filter clearing, no folder re-filtering).
- Remove the `tag_clicked` wiring from `TagCloudSettings` to `_on_tag_clicked_for_filter` — only the media info panel tag clicks should trigger the full filter flow.

### ✓ Step 5: Remove tags row from FolderFilters
Remove the `selected_tags_container` and related code from `FolderFilters` that was added for the prior tag-click implementation.
- Remove `selected_tags_container`, `selected_tags_layout`, `_selected_tags`, `selected_tags` property, `add_selected_tag()`, `clear_selected_tags()`, and the `selected_tags_container` widget from the layout in `folder_filter.py`.
- Remove the TagButton import if no longer needed.
- Update `AppContainer._on_tag_clicked_for_filter` to no longer call `folder_nav_filters.clear_selected_tags()` and `folder_nav_filters.add_selected_tag(tag)` — these are no longer needed since the tags row is removed.
- Update `folder_filter_filter.py` to remove tag-based filtering from criteria if present.
- Run `ruff check --fix` and `ruff format` to ensure lint/format compliance.