# -*- coding: utf-8 -*-
"""
资源路径工具
支持开发环境和 PyInstaller 打包环境
"""

import sys
import os


def resource_path(relative_path):
    """
    获取资源文件的绝对路径

    Args:
        relative_path: 相对路径

    Returns:
        资源文件的绝对路径

    注意:
        - 在开发环境中，返回相对于脚本的路径
        - 在 PyInstaller 打包环境中，返回临时目录中的路径
    """
    try:
        # PyInstaller 创建的临时文件夹，路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境，使用脚本所在目录的父目录
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)
