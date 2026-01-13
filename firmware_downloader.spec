# -*- mode: python ; coding: utf-8 -*-
"""
# pyinstaller firmware_downloader.spec
"""
"""
下载器 PyInstaller 打包配置
支持独立打包和集成打包
"""

import os
import sys

block_cipher = None

# 获取当前脚本目录
spec_dir = os.path.dirname(os.path.abspath(SPEC))

# 分析主程序
a = Analysis(
    ['firmware_downloader_dialog.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        # 添加资源文件
        (os.path.join(spec_dir, 'resources'), 'resources'),
    ],
    hiddenimports=[
        'firmware_downloader_project',
        'firmware_downloader_project.core',
        'firmware_downloader_project.widgets',
        'firmware_downloader_project.widgets.widgets',
        'firmware_downloader_project.widgets.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GHowe_Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(spec_dir, 'resources', 'HOWE_LOGO.ico') if os.path.exists(os.path.join(spec_dir, 'resources', 'HOWE_LOGO.ico')) else None,
)
