# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/MyVideoExplorer/main.py'],
    pathex=['./'],
    binaries=[],
    datas=[
        ( 'README.md', './' ),
        ( 'doc/', 'doc/' ),
        ( 'asset/app.png', 'asset/' ),
        ( 'asset/fonts/', 'asset/fonts/' ),
        ( 'cfg/defaults*.json', 'cfg/' ),
        ( 'src/MyVideoExplorer/db/migrations/*.sql', 'MyVideoExplorer/db/migrations/' ),
    ],
    hiddenimports=['uuid', '_uuid', 'duckdb', 'pandas'],
    collect_all=['duckdb'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtAxContainer',
        'PySide6.QtBluetooth',
        'PySide6.QtCharts',
        'PySide6.QtConcurrent',
        'PySide6.QtDataVisualization',
        'PySide6.QtDesigner',
        'PySide6.QtHelp',
        'PySide6.QtLocation',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNfc',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtPrintSupport',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickWidgets',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtStateMachine',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtTest',
        'PySide6.QtTextToSpeech',
        'PySide6.QtUiTools',
        'PySide6.QtVirtualKeyboard',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
        'PySide6.QtXml',
        'PySide6.QtXmlPatterns',
        'curses',
        'dbm',
        'distutils',
        'doctest',
        'ftplib',
        'html',
        'http',
        'lib2to3',
        'msilib',
        'nntplib',
        'pydoc',
        'pydoc_data',
        'setuptools',
        'smtplib',
        'sqlite3',
        'telnetlib',
        'test',
        'tkinter',
        'unittest',
        'wsgiref',
        'xmlrpc',
    ],
)

# -- start additional removals from build

# --- Strip unused Qt binaries & data that excludes can't touch ---
EXCLUDED_BINARIES = (
    'Qt6AxContainer',
    'Qt6Bluetooth',
    'Qt6Charts',
    'Qt6DataVisualization',
    'Qt6Designers',
    'Qt6Help',
    'Qt6Location',
    'Qt6Multimedia',
    'Qt6Nfc',
    'Qt6OpenGL',
    'Qt6Pdf',
    'Qt6Positioning',
    'Qt6PrintSupport',
    'Qt6Qml',
    'Qt6Quick',
    'Qt6RemoteObjects',
    'Qt6Scxml',
    'Qt6Sensors',
    'Qt6SerialPort',
    'Qt6ShaderTools',
    'Qt6StateMachine',
    'Qt6Test',
    'Qt6TextToSpeech',
    'Qt6VirtualKeyboard',
    'Qt6WebChannel',
    'Qt6WebEngine',
    'Qt6WebSockets',
    'Qt6Xml',
    'Qt63D',
)
EXCLUDED_BINARIES = tuple(b.lower() for b in EXCLUDED_BINARIES)

# Languages to KEEP in Qt translations (None = remove all)
# KEEP_LANGS = ('en', 'de', 'es')
KEEP_LANGS = ('en')

# Folder prefixes to drop entirely (QML + leftover Qt data)
EXCLUDED_DATA_PREFIXES = (
    'PySide6/qml',
    'PySide6/Qt/qml',
)

def _keep(item):
    """Filter predicate for a.binaries and a.datas tuples."""
    path = item[0].replace('\\', '/')
    path_lower = path.lower()

    name = path_lower.rsplit('/', 1)[-1]
    if name.startswith(EXCLUDED_BINARIES):
        return False

    if any(path_lower.startswith(p) for p in EXCLUDED_DATA_PREFIXES):
        return False

    if 'translations' in path_lower and path_lower.endswith('.qm'):
        if KEEP_LANGS is None:
            return False
        return any(f'_{lang}.' in path_lower for lang in KEEP_LANGS)

    return True

a.binaries = [x for x in a.binaries if _keep(x)]
a.datas = [x for x in a.datas if _keep(x)]

# -- end additional removals from build

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
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'qwindows.dll',
    ],
    console=False,
    icon='asset/app.ico',
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
