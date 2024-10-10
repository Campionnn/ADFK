# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\aweso\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\autoit\\', 'autoit'), ('C:\\Users\\aweso\\Desktop\\ADFK-dist\\ADFK\\memory_search.cp311-win_amd64.pyd', 'memory_search'), ('C:\\Users\\aweso\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\vgamepad\\win\\vigem\\client\\x64\\ViGEmClient.dll', 'vgamepad\\win\\vigem\\client\\x64')],
    hiddenimports=["memory_search", "autoit", "comtypes", "comtypes.gen", "comtypes.patcher", "comtypes.GUID", "comtypes.stream"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["config"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
