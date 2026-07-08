# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec del dashboard del terapeuta (onedir).
# Se construye en Windows (CI). build/libgamecore.dll debe existir antes de correr
# pyinstaller (CI: paso "Construir libgamecore.dll"). Correr desde la raiz del repo.
import os

raiz = os.path.abspath(os.getcwd())
dll = os.path.join(raiz, "build", "libgamecore.dll")

a = Analysis(
    ['dashboard/app.py'],
    pathex=['dashboard', 'simulator'],
    binaries=[],
    datas=[(dll, '.')] if os.path.exists(dll) else [],
    hiddenimports=['core_bridge', 'fuente', 'sesion', 'storage', 'reports',
                   'paneles', 'analitica', 'estilo', 'robustez', 'puertos'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
          name='TapeteDashboard', console=False)
coll = COLLECT(exe, a.binaries, a.datas, name='TapeteDashboard')
