# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=['./'],
    binaries=[],
    datas=[
        ( 'README.md', './' ),
        ( 'cfg/defaults*.json', 'cfg' ),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'sqlite3.dll',
        'tcl85.dll',
        'tk85.dll',
    ],
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    exclude_binaries=True,
    name='MyVideoExplorer',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'qwindows.dll',
    ],
    console=False,
    icon='assets/app.ico',
    onefile=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'qwindows.dll',
    ],
    name='MyVideoExplorer',
)
