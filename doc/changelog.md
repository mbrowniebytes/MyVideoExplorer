## Change Log

---

### 2026-0#-##

- fix app launch of last size, last pos
- internal:
    - remove black, mypy in favor of existing ruff and new ty
    - code quality ty checks - pending


release - [MyVideoExplorer-20260###-0.004 ](https://github.com/mbrowniebytes/MyVideoExplorer/releases/tag/20260###-0.004)

### 2026-07-14

- better handling of initial launch with no Media Folders
- on app start or Folder refresh, add an option in App Settings to auto select the Prior Folder or the First Folder
- add new cfg/settings_state.json
- to the Folder list, add Forward, Backward, and Random buttons
- add Font selection in UI Settings
- add Launch App Size selection in App Settings
- add Launch App Position selection in App Settings
- add checkbox styling
- internal:
    - remove structlog in favor of std logger
    - remove BaseWidget
    - on save settings, do not create a backup if settings have not changed from last backup
    - font refresh fix
    - code quality ruff checks
    - optimize build spec resulting in a slightly smaller build, using less memory

release - [MyVideoExplorer-20260714-0.003 ](https://github.com/mbrowniebytes/MyVideoExplorer/releases/tag/20260714-0.003)

---

### 2026-06-24

- handle network shares
- show loading media folder
- auto select first folder
- display media icon in folder list
- tweak scroll bars, title style
- auto select poster first
- optimize code, signals
- better thread scanning of media folders
- connect filter settings
- fix widget flicker/reinitialize when scroll quickly
- better app error handling
- better theme/font size handling
- add app icons
- add font loading
- code quality ruff checks
- re-format w/ PyCharm
- update readme

release - [MyVideoExplorer-20260624-0.002 ](https://github.com/mbrowniebytes/MyVideoExplorer/releases/tag/20260624-0.002)

---

### 2026-06-15

- initial release

release - [MyVideoExplorer-20260615-0.001 ](https://github.com/mbrowniebytes/MyVideoExplorer/releases/tag/20260615-0.001)
