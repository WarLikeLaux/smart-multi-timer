# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/resources/images/*.ico', 'resources/images'),
        ('src/resources/images/*.jpeg', 'resources/images'),
        ('src/resources/sounds/*.mp3', 'resources/sounds'),
    ],
    hiddenimports=['pygame.mixer'],
    excludes=['numpy'],
    noarchive=True,
)

pyz = PYZ(a.pure, a.zipped_data, compress=False)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Мульти-таймер v3',
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir='.',
    console=False,
    icon='app.ico',
)