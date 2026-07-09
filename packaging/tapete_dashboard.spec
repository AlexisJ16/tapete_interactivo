# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec del dashboard del terapeuta (onedir).
# Se construye en Windows (CI). build/libgamecore.dll debe existir antes de correr
# pyinstaller (CI: paso "Construir libgamecore.dll").
# Las rutas se anclan a la RAIZ del repo via SPECPATH (dir de este .spec), no al
# cwd: en un .spec las rutas relativas de Analysis se resuelven contra el dir del
# spec (packaging/), lo que rompia el entry. Absolutas => funciona desde cualquier cwd.
import os

raiz = os.path.abspath(os.path.join(SPECPATH, os.pardir))
dll = os.path.join(raiz, "build", "libgamecore.dll")

a = Analysis(
    [os.path.join(raiz, 'dashboard', 'app.py')],
    pathex=[os.path.join(raiz, 'dashboard'), os.path.join(raiz, 'simulator')],
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
