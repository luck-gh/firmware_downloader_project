#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义控件
"""

from PyQt5.QtWidgets import (QLabel, QTextEdit, QProgressBar, QWidget,
                             QVBoxLayout, QHBoxLayout, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont

# 导入验证函数
try:
    from ..core.protocol import ProtocolHandler
except ImportError:
    try:
        from core.protocol import ProtocolHandler
    except ImportError:
        from firmware_downloader_project.core.protocol import ProtocolHandler


class ValidatedLineEdit(QLineEdit):
    """带格式验证的输入框"""

    def __init__(self, data_format="HEX", parent=None):
        super().__init__(parent)
        self.data_format = data_format
        self.textChanged.connect(self._validate_input)

    def set_format(self, data_format: str):
        """设置验证格式"""
        self.data_format = data_format
        self._validate_input()

    def _validate_input(self):
        """验证输入并设置样式"""
        text = self.text()

        if not text:
            # 空输入，使用默认样式
            self.setStyleSheet("")
            self.setToolTip("")
            return

        is_valid, error_msg = ProtocolHandler.validate_input_format(text, self.data_format)

        if is_valid:
            # 有效输入，绿色边框
            self.setStyleSheet("QLineEdit { border: 2px solid #4CAF50; }")
            self.setToolTip("格式正确")
        else:
            # 无效输入，红色边框
            self.setStyleSheet("QLineEdit { border: 2px solid #F44336; }")
            self.setToolTip(f"格式错误: {error_msg}")


class FileDropLabel(QLabel):
    """支持拖放文件的标签控件"""

    file_dropped = pyqtSignal(str)  # 文件路径信号

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                border-radius: 5px;
                background-color: #f5f5f5;
                padding: 20px;
                min-height: 80px;
            }
            QLabel:hover {
                border-color: #555;
                background-color: #e8e8e8;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                    background-color: #e8f5e9;
                    padding: 20px;
                    min-height: 80px;
                }
            """)

    def dragLeaveEvent(self, event):
        """拖出事件"""
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                border-radius: 5px;
                background-color: #f5f5f5;
                padding: 20px;
                min-height: 80px;
            }
            QLabel:hover {
                border-color: #555;
                background-color: #e8e8e8;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            # 只处理第一个文件
            file_path = files[0]
            if file_path.lower().endswith('.bin'):
                self.file_dropped.emit(file_path)
                self.setText(f"✓ 已选择文件\n{file_path}")
            else:
                self.setText("✗ 仅支持 .bin 文件")

        # 恢复样式
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                border-radius: 5px;
                background-color: #f5f5f5;
                padding: 20px;
                min-height: 80px;
            }
            QLabel:hover {
                border-color: #555;
                background-color: #e8e8e8;
            }
        """)


class LogWidget(QTextEdit):
    """日志显示控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(200)

        # 设置等宽字体
        font = QFont("Consolas")
        font.setPointSize(9)
        self.setFont(font)

        # 日志级别颜色
        self.level_colors = {
            'INFO': '#000000',
            'SUCCESS': '#4CAF50',
            'WARNING': '#FF9800',
            'ERROR': '#F44336',
            'DEBUG': '#9E9E9E'  # 灰色用于调试信息
        }

        # 日志级别过滤
        self.enabled_levels = {
            'INFO': False,
            'SUCCESS': True,
            'WARNING': True,
            'ERROR': True,
            'DEBUG': False
        }

    def set_level_filter(self, level: str, enabled: bool):
        """
        设置日志级别过滤

        Args:
            level: 日志级别
            enabled: 是否启用该级别
        """
        if level in self.enabled_levels:
            self.enabled_levels[level] = enabled

    def append_log(self, level: str, message: str):
        """
        添加日志

        Args:
            level: 日志级别 (INFO/SUCCESS/WARNING/ERROR/DEBUG)
            message: 日志消息
        """
        # 检查是否启用该日志级别
        if not self.enabled_levels.get(level, True):
            return

        color = self.level_colors.get(level, '#000000')
        html = f'<span style="color: {color};">[{level}] {message}</span>'
        self.append(html)

        # 自动滚动到底部
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear_log(self):
        """清空日志"""
        self.clear()


class ProgressWidget(QWidget):
    """进度显示控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        # 统计信息
        stats_layout = QHBoxLayout()

        self.packets_label = QLabel("已发送: 0 / 0 包")
        self.speed_label = QLabel("速度: 0 KB/s")
        self.time_label = QLabel("用时: 0 秒")

        stats_layout.addWidget(self.packets_label)
        stats_layout.addWidget(self.speed_label)
        stats_layout.addWidget(self.time_label)
        stats_layout.addStretch()

        layout.addLayout(stats_layout)

    def update_progress(self, current: int, total: int, percentage: int):
        """
        更新进度

        Args:
            current: 当前包数
            total: 总包数
            percentage: 百分比
        """
        self.progress_bar.setValue(percentage)
        self.packets_label.setText(f"已发送: {current} / {total} 包")

    def update_speed(self, speed_kbps: float):
        """更新速度"""
        self.speed_label.setText(f"速度: {speed_kbps:.2f} KB/s")

    def update_time(self, elapsed_seconds: int):
        """更新用时"""
        self.time_label.setText(f"用时: {elapsed_seconds} 秒")

    def reset(self):
        """重置进度"""
        self.progress_bar.setValue(0)
        self.packets_label.setText("已发送: 0 / 0 包")
        self.speed_label.setText("速度: 0 KB/s")
        self.time_label.setText("用时: 0 秒")
