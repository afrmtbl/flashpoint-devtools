# -*- mode: python -*-
import os
import sys
import pathlib

drive_letter = pathlib.Path.home().drive
sys.path.insert(0, f"{drive_letter}/Windows/System32/downlevel")

block_cipher = None


a = Analysis(['devtools.py', 'devtools.spec'],
             pathex=[os.getcwd()],
             binaries=[],
             datas=[("icon.ico", ".")],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='FlashpointDevTools',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon="icon.ico" )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='devtools')
