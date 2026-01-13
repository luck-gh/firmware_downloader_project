#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
固件下载工具 - 主对话框
"""

import os
import sys
import time
import serial.tools.list_ports
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QLineEdit, QPushButton, QComboBox,
                             QSpinBox, QCheckBox, QFileDialog, QMessageBox,
                             QApplication, QWidget, QSizePolicy, QScrollArea)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

# 多级导入支持
try:
    from .widgets.widgets import FileDropLabel, LogWidget, ProgressWidget, ValidatedLineEdit
    from .core.downloader import FirmwareDownloader
    from .core.protocol import ProtocolHandler
except ImportError:
    try:
        from widgets.widgets import FileDropLabel, LogWidget, ProgressWidget, ValidatedLineEdit
        from core.downloader import FirmwareDownloader
        from core.protocol import ProtocolHandler
    except ImportError:
        from firmware_downloader_project.widgets.widgets import FileDropLabel, LogWidget, ProgressWidget, ValidatedLineEdit
        from firmware_downloader_project.core.downloader import FirmwareDownloader
        from firmware_downloader_project.core.protocol import ProtocolHandler


class DownloadThread(QThread):
    """下载线程"""

    progress_signal = pyqtSignal(int, int, int)  # current, total, percentage
    log_signal = pyqtSignal(str, str)  # level, message
    finished_signal = pyqtSignal(bool, str)  # success, message
    speed_signal = pyqtSignal(float)  # speed in KB/s
    time_signal = pyqtSignal(int)  # elapsed time in seconds

    def __init__(self, downloader: FirmwareDownloader, firmware_path: str):
        super().__init__()
        self.downloader = downloader
        self.firmware_path = firmware_path
        self.start_time = 0
        self.bytes_sent = 0

    def run(self):
        """运行下载"""
        self.start_time = time.time()

        success, message = self.downloader.download(
            self.firmware_path,
            progress_callback=self._on_progress,
            log_callback=self._on_log
        )

        self.finished_signal.emit(success, message)

    def _on_progress(self, current: int, total: int, message: str):
        """进度回调"""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_signal.emit(current, total, percentage)

        # 计算速度
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            # 假设每包大小
            packet_size = self.downloader.download_config.get('packet_size', 256)
            bytes_sent = current * packet_size
            speed_kbps = (bytes_sent / 1024) / elapsed
            self.speed_signal.emit(speed_kbps)

        # 更新时间
        self.time_signal.emit(int(elapsed))

    def _on_log(self, level: str, message: str):
        """日志回调"""
        self.log_signal.emit(level, message)


class FirmwareDownloaderDialog(QDialog):
    """固件下载工具对话框"""

    def __init__(
        self,
        parent=None,
        initial_file: str = "",
        # 串口配置（可选，用于从主工具传递）
        port: str = "",
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: float = 1,
        # 下载基本配置
        packet_size: int = 256,
        start_command: str = "download 0\\r\\n",
        add_packet_crc: bool = False,
        packet_crc_type: str = "CRC16-MODBUS",
        # 开始命令 ACK 配置
        wait_start_ack: bool = True,
        start_ack_timeout: int = 1000,
        start_ack_check_length: bool = False,
        start_ack_expected_length: int = 1,
        start_ack_check_data: bool = True,
        start_ack_expected_data: str = "download 0\\r\\nOK\\r\\n",
        start_ack_data_format: str = "ASCII",
        start_ack_check_mode: str = "AND",
        # 数据包 ACK 配置
        wait_packet_ack: bool = True,
        packet_ack_timeout: int = 1000,
        packet_ack_check_length: bool = False,
        packet_ack_expected_length: int = 1,
        packet_ack_check_data: bool = True,
        packet_ack_expected_data: str = "OK\\r\\n",
        packet_ack_data_format: str = "ASCII",
        packet_ack_check_crc: bool = False,
        packet_ack_crc_type: str = "CRC16-MODBUS",
        packet_ack_check_mode: str = "AND",
        # 末尾数据包 ACK 配置
        wait_last_packet_ack: bool = True,
        last_packet_ack_timeout: int = 5000,
        last_packet_ack_check_length: bool = False,
        last_packet_ack_expected_length: int = 1,
        last_packet_ack_check_data: bool = True,
        last_packet_ack_expected_data: str = "END\\r\\n",
        last_packet_ack_data_format: str = "ASCII",
        last_packet_ack_check_crc: bool = False,
        last_packet_ack_crc_type: str = "CRC16-MODBUS",
        last_packet_ack_check_mode: str = "AND",
        # 结尾字符串配置
        send_end_string: bool = True,
        end_string: str = "?\\r\\n"
    ):
        super().__init__(parent)

        # 保存初始参数
        self.initial_file = initial_file
        self.initial_port_config = {
            'port': port,
            'baudrate': baudrate,
            'bytesize': bytesize,
            'parity': parity,
            'stopbits': stopbits
        }
        self.initial_download_config = {
            'start_command': start_command,
            'packet_size': packet_size,
            'add_packet_crc': add_packet_crc,
            'packet_crc_type': packet_crc_type,
            # 开始命令 ACK
            'wait_start_ack': wait_start_ack,
            'start_ack_timeout': start_ack_timeout,
            'start_ack_check_length': start_ack_check_length,
            'start_ack_expected_length': start_ack_expected_length,
            'start_ack_check_data': start_ack_check_data,
            'start_ack_expected_data': start_ack_expected_data,
            'start_ack_data_format': start_ack_data_format,
            'start_ack_check_mode': start_ack_check_mode,
            # 数据包 ACK
            'wait_packet_ack': wait_packet_ack,
            'packet_ack_timeout': packet_ack_timeout,
            'packet_ack_check_length': packet_ack_check_length,
            'packet_ack_expected_length': packet_ack_expected_length,
            'packet_ack_check_data': packet_ack_check_data,
            'packet_ack_expected_data': packet_ack_expected_data,
            'packet_ack_data_format': packet_ack_data_format,
            'packet_ack_check_crc': packet_ack_check_crc,
            'packet_ack_crc_type': packet_ack_crc_type,
            'packet_ack_check_mode': packet_ack_check_mode,
            # 末尾数据包 ACK
            'wait_last_packet_ack': wait_last_packet_ack,
            'last_packet_ack_timeout': last_packet_ack_timeout,
            'last_packet_ack_check_length': last_packet_ack_check_length,
            'last_packet_ack_expected_length': last_packet_ack_expected_length,
            'last_packet_ack_check_data': last_packet_ack_check_data,
            'last_packet_ack_expected_data': last_packet_ack_expected_data,
            'last_packet_ack_data_format': last_packet_ack_data_format,
            'last_packet_ack_check_crc': last_packet_ack_check_crc,
            'last_packet_ack_crc_type': last_packet_ack_crc_type,
            'last_packet_ack_check_mode': last_packet_ack_check_mode,
            # 结尾字符串
            'send_end_string': send_end_string,
            'end_string': end_string
        }

        self.download_thread = None
        self.downloader = None

        self.init_ui()
        self.apply_initial_config()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("固件下载工具 - GHowe")
        self.setMinimumWidth(700)
        # 移除固定高度，让窗口根据内容自适应
        # self.setMinimumHeight(750)

        layout = QVBoxLayout(self)

        # === 串口配置 ===
        port_group = self._create_port_group()
        layout.addWidget(port_group)

        # === 文件选择 ===
        file_group = self._create_file_group()
        layout.addWidget(file_group)

        # === 下载配置（使用滚动区域）===
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        config_scroll.setFrameShape(QScrollArea.NoFrame)

        config_container = QWidget()
        config_container_layout = QVBoxLayout(config_container)
        config_container_layout.setContentsMargins(0, 0, 0, 0)

        config_group = self._create_config_group()
        config_container_layout.addWidget(config_group)

        config_scroll.setWidget(config_container)
        layout.addWidget(config_scroll, 1)  # 添加拉伸因子，使其可以扩展

        # === 进度显示 ===
        progress_group = self._create_progress_group()
        layout.addWidget(progress_group)

        # === 日志输出 ===
        log_group = self._create_log_group()
        layout.addWidget(log_group)

        # === 按钮 ===
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)

    def _create_port_group(self) -> QGroupBox:
        """创建串口配置组"""
        group = QGroupBox("串口配置")
        layout = QVBoxLayout(group)

        # 第一行: 端口和波特率
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("端口:"))
        self.port_combo = QComboBox()
        self.port_combo.installEventFilter(self)    # 禁用滚轮
        self.port_combo.setMinimumWidth(120)
        self._refresh_ports()
        row1.addWidget(self.port_combo)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setMaximumWidth(60)
        refresh_btn.clicked.connect(self._refresh_ports)
        row1.addWidget(refresh_btn)

        row1.addWidget(QLabel("波特率:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baudrate_combo.setCurrentText("115200")
        row1.addWidget(self.baudrate_combo)

        row1.addStretch()
        layout.addLayout(row1)

        # 第二行: 数据位、停止位、校验位
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("数据位:"))
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["5", "6", "7", "8"])
        self.bytesize_combo.setCurrentText("8")
        row2.addWidget(self.bytesize_combo)

        row2.addWidget(QLabel("停止位:"))
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        row2.addWidget(self.stopbits_combo)

        row2.addWidget(QLabel("校验位:"))
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Odd", "Even", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")
        row2.addWidget(self.parity_combo)

        row2.addStretch()
        layout.addLayout(row2)

        return group

    def _create_file_group(self) -> QGroupBox:
        """创建文件选择组"""
        group = QGroupBox("文件选择")
        layout = QVBoxLayout(group)

        # 拖放区域
        self.file_drop_label = FileDropLabel("📁 拖放 .bin 文件到此处或点击浏览按钮")
        self.file_drop_label.file_dropped.connect(self._on_file_dropped)
        layout.addWidget(self.file_drop_label)

        # 文件路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("文件路径:"))
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("请选择 .bin 文件")
        path_layout.addWidget(self.file_path_edit)

        browse_btn = QPushButton("浏览...")
        browse_btn.setMaximumWidth(70)
        browse_btn.clicked.connect(self._browse_file)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        return group

    def _create_config_group(self) -> QGroupBox:
        """创建下载配置组"""
        group = QGroupBox("下载配置")
        layout = QVBoxLayout(group)

        # 基本配置
        basic_layout = QHBoxLayout()
        basic_layout.addWidget(QLabel("开始命令:"))
        self.start_cmd_edit = QLineEdit()
        self.start_cmd_edit.setText("START_DOWNLOAD")
        basic_layout.addWidget(self.start_cmd_edit)

        basic_layout.addWidget(QLabel("包大小:"))
        self.packet_size_spin = QSpinBox()
        self.packet_size_spin.setRange(1, 4096)
        self.packet_size_spin.setValue(256)
        self.packet_size_spin.setSuffix(" Bytes")
        basic_layout.addWidget(self.packet_size_spin)

        layout.addLayout(basic_layout)

        # 数据包 CRC
        packet_crc_layout = QHBoxLayout()
        self.packet_crc_check = QCheckBox("发送数据包时追加 CRC")
        packet_crc_layout.addWidget(self.packet_crc_check)

        packet_crc_layout.addWidget(QLabel("类型:"))
        self.packet_crc_type_combo = QComboBox()
        self.packet_crc_type_combo.addItems(["CRC16-MODBUS", "CRC16-CCITT", "CRC16-XMODEM", "CRC32"])
        packet_crc_layout.addWidget(self.packet_crc_type_combo)
        packet_crc_layout.addStretch()

        layout.addLayout(packet_crc_layout)

        # # === 分隔线：开始命令 ACK ===
        # start_ack_separator = QLabel("━━━━━━━━━ 开始命令 ACK 配置 ━━━━━━━━━")
        # start_ack_separator.setAlignment(Qt.AlignCenter)
        # start_ack_separator.setStyleSheet("color: #666; font-weight: bold;")
        # layout.addWidget(start_ack_separator)

        # 创建开始命令 ACK 配置（不需要CRC）
        start_ack_check, start_ack_widget, start_ack_widgets = self._create_ack_config_section(
            prefix="start",
            title="等待开始命令 ACK",
            enable_crc=False,
            default_timeout=1000
        )
        layout.addWidget(start_ack_widget)  # 只添加 wrapper，checkbox 已经在里面了

        # 保存控件引用
        self.start_ack_check = start_ack_check
        self.start_ack_widget = start_ack_widget
        self.start_ack_timeout_spin = start_ack_widgets['timeout_spin']
        self.start_ack_mode_combo = start_ack_widgets['mode_combo']
        self.start_ack_length_check = start_ack_widgets['length_check']
        self.start_ack_length_spin = start_ack_widgets['length_spin']
        self.start_ack_data_check = start_ack_widgets['data_check']
        self.start_ack_data_edit = start_ack_widgets['data_edit']
        self.start_ack_format_combo = start_ack_widgets['format_combo']

        # # === 分隔线：数据包 ACK ===
        # packet_ack_separator = QLabel("━━━━━━━━━ 数据包 ACK 配置 ━━━━━━━━━")
        # packet_ack_separator.setAlignment(Qt.AlignCenter)
        # packet_ack_separator.setStyleSheet("color: #666; font-weight: bold;")
        # layout.addWidget(packet_ack_separator)

        # 创建数据包 ACK 配置（包含CRC）
        packet_ack_check, packet_ack_widget, packet_ack_widgets = self._create_ack_config_section(
            prefix="packet",
            title="等待数据包 ACK",
            enable_crc=True,
            default_timeout=1000
        )
        layout.addWidget(packet_ack_widget)  # 只添加 wrapper，checkbox 已经在里面了

        # 保存控件引用
        self.packet_ack_check = packet_ack_check
        self.packet_ack_widget = packet_ack_widget
        self.packet_ack_timeout_spin = packet_ack_widgets['timeout_spin']
        self.packet_ack_mode_combo = packet_ack_widgets['mode_combo']
        self.packet_ack_length_check = packet_ack_widgets['length_check']
        self.packet_ack_length_spin = packet_ack_widgets['length_spin']
        self.packet_ack_data_check = packet_ack_widgets['data_check']
        self.packet_ack_data_edit = packet_ack_widgets['data_edit']
        self.packet_ack_format_combo = packet_ack_widgets['format_combo']
        self.packet_ack_crc_check = packet_ack_widgets['crc_check']
        self.packet_ack_crc_type_combo = packet_ack_widgets['crc_type_combo']

        # # === 分隔线：末尾数据包 ACK ===
        # last_packet_ack_separator = QLabel("━━━━━━━━━ 末尾数据包 ACK 配置 ━━━━━━━━━")
        # last_packet_ack_separator.setAlignment(Qt.AlignCenter)
        # last_packet_ack_separator.setStyleSheet("color: #666; font-weight: bold;")
        # layout.addWidget(last_packet_ack_separator)

        # 创建末尾数据包 ACK 配置（包含CRC）
        last_packet_ack_check, last_packet_ack_widget, last_packet_ack_widgets = self._create_ack_config_section(
            prefix="last_packet",
            title="等待末尾数据包 ACK",
            enable_crc=True,
            default_timeout=1000
        )
        layout.addWidget(last_packet_ack_widget)  # 只添加 wrapper，checkbox 已经在里面了

        # 保存控件引用
        self.last_packet_ack_check = last_packet_ack_check
        self.last_packet_ack_widget = last_packet_ack_widget
        self.last_packet_ack_timeout_spin = last_packet_ack_widgets['timeout_spin']
        self.last_packet_ack_mode_combo = last_packet_ack_widgets['mode_combo']
        self.last_packet_ack_length_check = last_packet_ack_widgets['length_check']
        self.last_packet_ack_length_spin = last_packet_ack_widgets['length_spin']
        self.last_packet_ack_data_check = last_packet_ack_widgets['data_check']
        self.last_packet_ack_data_edit = last_packet_ack_widgets['data_edit']
        self.last_packet_ack_format_combo = last_packet_ack_widgets['format_combo']
        self.last_packet_ack_crc_check = last_packet_ack_widgets['crc_check']
        self.last_packet_ack_crc_type_combo = last_packet_ack_widgets['crc_type_combo']

        # === 结尾字符串配置 ===
        end_string_layout = QHBoxLayout()
        self.send_end_string_check = QCheckBox("发送结尾字符串")
        end_string_layout.addWidget(self.send_end_string_check)
        end_string_layout.addWidget(QLabel("结尾字符串:"))
        self.end_string_edit = QLineEdit()
        self.end_string_edit.setPlaceholderText("支持转义字符: \\r\\n\\t\\x##")
        end_string_layout.addWidget(self.end_string_edit)
        layout.addLayout(end_string_layout)

        return group

    def _create_ack_config_section(
        self,
        prefix: str,
        title: str,
        enable_crc: bool = True,
        default_timeout: int = 1000
    ) -> tuple:
        """
        创建通用的 ACK 配置区域（代码复用）

        Args:
            prefix: 控件名称前缀 (如 "start" 或 "packet")
            title: 显示标题
            enable_crc: 是否启用 CRC 校验选项
            default_timeout: 默认超时时间

        Returns:
            (enable_check, config_widget, widgets_dict)
        """
        # 创建包装容器
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(5)

        # 标题行 - 包含复选框和折叠按钮
        title_widget = QWidget()
        title_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(5, 5, 5, 5)

        # 启用复选框
        enable_check = QCheckBox(title)
        title_layout.addWidget(enable_check)

        # 折叠/展开按钮
        toggle_button = QPushButton("▼ 展开")
        toggle_button.setMaximumWidth(80)
        toggle_button.setCheckable(True)
        toggle_button.setChecked(False)  # 默认折叠
        title_layout.addWidget(toggle_button)
        title_layout.addStretch()

        wrapper_layout.addWidget(title_widget)

        # 配置容器
        config_widget = QWidget()
        config_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        config_widget.setEnabled(False)
        config_widget.setVisible(False)  # 默认隐藏（折叠状态）
        config_widget.setStyleSheet("""
            QWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
        """)
        config_layout = QVBoxLayout(config_widget)
        config_layout.setContentsMargins(10, 10, 10, 10)
        config_layout.setSpacing(8)

        # 折叠/展开逻辑
        def toggle_visibility():
            is_visible = config_widget.isVisible()
            config_widget.setVisible(not is_visible)
            toggle_button.setText("▲ 收起" if not is_visible else "▼ 展开")
            # 强制更新父容器布局
            parent = wrapper.parent()
            if parent:
                parent.updateGeometry()

        toggle_button.clicked.connect(toggle_visibility)

        # 超时和逻辑
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("超时:"))
        timeout_spin = QSpinBox()
        timeout_spin.setRange(100, 10000)
        timeout_spin.setValue(default_timeout)
        timeout_spin.setSuffix(" ms")
        timeout_spin.installEventFilter(self)  # 禁用滚轮
        timeout_layout.addWidget(timeout_spin)

        timeout_layout.addWidget(QLabel("判断逻辑:"))
        mode_combo = QComboBox()
        mode_combo.addItems(["全部满足 (AND)", "任一满足 (OR)"])
        mode_combo.installEventFilter(self)  # 禁用滚轮
        timeout_layout.addWidget(mode_combo)
        timeout_layout.addStretch()
        config_layout.addLayout(timeout_layout)

        # 长度判断
        length_layout = QHBoxLayout()
        length_check = QCheckBox("长度判断")
        length_layout.addWidget(length_check)
        length_layout.addWidget(QLabel("预期长度:"))
        length_spin = QSpinBox()
        length_spin.setRange(1, 256)
        length_spin.setValue(1)
        length_spin.setSuffix(" Bytes")
        length_spin.installEventFilter(self)  # 禁用滚轮
        length_layout.addWidget(length_spin)
        length_layout.addStretch()
        config_layout.addLayout(length_layout)

        # 数据匹配判断
        data_layout = QHBoxLayout()
        data_check = QCheckBox("数据匹配")
        data_layout.addWidget(data_check)
        data_layout.addWidget(QLabel("预期数据:"))

        # 使用带验证的输入框
        data_edit = ValidatedLineEdit("HEX")
        data_edit.setText("0x06")
        data_edit.setPlaceholderText("支持转义字符: \\r\\n\\t\\x##")
        data_layout.addWidget(data_edit)

        data_layout.addWidget(QLabel("格式:"))
        format_combo = QComboBox()
        format_combo.addItems(["HEX", "ASCII", "DEC"])
        format_combo.installEventFilter(self)  # 禁用滚轮

        # 格式改变时更新验证规则和提示
        def on_format_changed():
            fmt = format_combo.currentText()
            data_edit.set_format(fmt)
            if fmt == "HEX":
                data_edit.setPlaceholderText("如: 0x06 或 06 AA BB")
            elif fmt == "ASCII":
                data_edit.setPlaceholderText("支持转义字符: \\r\\n\\t\\x##")
            else:  # DEC
                data_edit.setPlaceholderText("如: 6 170 187 (空格分隔)")

        format_combo.currentTextChanged.connect(on_format_changed)
        data_layout.addWidget(format_combo)
        config_layout.addLayout(data_layout)

        # CRC 校验判断（可选）
        crc_check = None
        crc_type_combo = None
        if enable_crc:
            crc_layout = QHBoxLayout()
            crc_check = QCheckBox("CRC 校验")
            crc_layout.addWidget(crc_check)
            crc_layout.addWidget(QLabel("类型:"))
            crc_type_combo = QComboBox()
            crc_type_combo.addItems(["CRC16-MODBUS", "CRC16-CCITT", "CRC16-XMODEM", "CRC32"])
            crc_type_combo.installEventFilter(self)  # 禁用滚轮
            crc_layout.addWidget(crc_type_combo)
            crc_layout.addStretch()
            config_layout.addLayout(crc_layout)

        # 连接启用复选框
        enable_check.stateChanged.connect(
            lambda state: config_widget.setEnabled(state == Qt.Checked)
        )

        # 将配置容器添加到包装器
        wrapper_layout.addWidget(config_widget)

        # 返回控件字典
        widgets = {
            'enable_check': enable_check,
            'config_widget': config_widget,
            'timeout_spin': timeout_spin,
            'mode_combo': mode_combo,
            'length_check': length_check,
            'length_spin': length_spin,
            'data_check': data_check,
            'data_edit': data_edit,
            'format_combo': format_combo,
            'crc_check': crc_check,
            'crc_type_combo': crc_type_combo,
            'wrapper': wrapper,
            'toggle_button': toggle_button
        }

        return enable_check, wrapper, widgets

    def _create_progress_group(self) -> QGroupBox:
        """创建进度显示组"""
        group = QGroupBox("下载进度")
        layout = QVBoxLayout(group)

        self.progress_widget = ProgressWidget()
        layout.addWidget(self.progress_widget)

        return group

    def _create_log_group(self) -> QGroupBox:
        """创建日志输出组"""
        group = QGroupBox("日志输出")
        layout = QVBoxLayout(group)

        # 日志级别过滤控件
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日志过滤:"))

        # 创建日志级别复选框（成功和错误不可配置，始终显示）
        self.log_level_checks = {}
        log_levels = [
            ('WARNING', '警告', True),
            ('INFO', '信息', False),
            ('DEBUG', '调试', False)
        ]

        for level, label, default_checked in log_levels:
            check = QCheckBox(label)
            check.setChecked(default_checked)
            check.stateChanged.connect(
                lambda state, lv=level: self._on_log_filter_changed(lv, state == Qt.Checked)
            )
            self.log_level_checks[level] = check
            filter_layout.addWidget(check)

        # 添加提示标签
        hint_label = QLabel("(成功/错误始终显示)")
        hint_label.setStyleSheet("color: #666; font-size: 9pt;")
        filter_layout.addWidget(hint_label)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 日志显示控件
        self.log_widget = LogWidget()
        layout.addWidget(self.log_widget)

        return group

    def _on_log_filter_changed(self, level: str, enabled: bool):
        """日志过滤改变回调"""
        self.log_widget.set_level_filter(level, enabled)

    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮布局"""
        layout = QHBoxLayout()

        self.start_btn = QPushButton("开始下载")
        self.start_btn.clicked.connect(self.start_download)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_download)
        layout.addWidget(self.stop_btn)

        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.log_widget.clear_log)
        layout.addWidget(clear_log_btn)

        layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return layout

    def apply_initial_config(self):
        """应用初始配置"""
        # 文件路径
        if self.initial_file:
            # 标准化路径
            normalized_path = os.path.normpath(self.initial_file)
            self.file_path_edit.setText(normalized_path)
            if os.path.exists(normalized_path):
                self.file_drop_label.setText(f"✓ 已选择文件\n{os.path.basename(normalized_path)}")
            else:
                self.file_drop_label.setText(f"⚠ 文件不存在\n{normalized_path}")

        # 串口配置
        if self.initial_port_config.get('port'):
            # 使用 MatchContains 来匹配端口号
            port = self.initial_port_config['port']
            index = -1
            for i in range(self.port_combo.count()):
                if port in self.port_combo.itemText(i):
                    index = i
                    break
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

        if self.initial_port_config.get('baudrate'):
            self.baudrate_combo.setCurrentText(str(self.initial_port_config['baudrate']))

        # 下载基本配置
        self.start_cmd_edit.setText(self.initial_download_config.get('start_command', 'START_DOWNLOAD'))
        self.packet_size_spin.setValue(self.initial_download_config.get('packet_size', 256))

        # 数据包 CRC
        self.packet_crc_check.setChecked(self.initial_download_config.get('add_packet_crc', False))
        self.packet_crc_type_combo.setCurrentText(self.initial_download_config.get('packet_crc_type', 'CRC16-MODBUS'))

        # === 开始命令 ACK 配置 ===
        self.start_ack_check.setChecked(self.initial_download_config.get('wait_start_ack', False))
        self.start_ack_timeout_spin.setValue(self.initial_download_config.get('start_ack_timeout', 1000))
        self.start_ack_length_check.setChecked(self.initial_download_config.get('start_ack_check_length', True))
        self.start_ack_length_spin.setValue(self.initial_download_config.get('start_ack_expected_length', 1))
        self.start_ack_data_check.setChecked(self.initial_download_config.get('start_ack_check_data', False))
        self.start_ack_data_edit.setText(self.initial_download_config.get('start_ack_expected_data', '0x06'))
        self.start_ack_format_combo.setCurrentText(self.initial_download_config.get('start_ack_data_format', 'HEX'))

        start_ack_mode_text = "全部满足 (AND)" if self.initial_download_config.get('start_ack_check_mode', 'AND') == 'AND' else "任一满足 (OR)"
        self.start_ack_mode_combo.setCurrentText(start_ack_mode_text)

        # === 数据包 ACK 配置 ===
        self.packet_ack_check.setChecked(self.initial_download_config.get('wait_packet_ack', False))
        self.packet_ack_timeout_spin.setValue(self.initial_download_config.get('packet_ack_timeout', 1000))
        self.packet_ack_length_check.setChecked(self.initial_download_config.get('packet_ack_check_length', True))
        self.packet_ack_length_spin.setValue(self.initial_download_config.get('packet_ack_expected_length', 1))
        self.packet_ack_data_check.setChecked(self.initial_download_config.get('packet_ack_check_data', False))
        self.packet_ack_data_edit.setText(self.initial_download_config.get('packet_ack_expected_data', '0x06'))
        self.packet_ack_format_combo.setCurrentText(self.initial_download_config.get('packet_ack_data_format', 'HEX'))
        self.packet_ack_crc_check.setChecked(self.initial_download_config.get('packet_ack_check_crc', False))
        self.packet_ack_crc_type_combo.setCurrentText(self.initial_download_config.get('packet_ack_crc_type', 'CRC16-MODBUS'))

        packet_ack_mode_text = "全部满足 (AND)" if self.initial_download_config.get('packet_ack_check_mode', 'AND') == 'AND' else "任一满足 (OR)"
        self.packet_ack_mode_combo.setCurrentText(packet_ack_mode_text)

        # === 末尾数据包 ACK 配置 ===
        self.last_packet_ack_check.setChecked(self.initial_download_config.get('wait_last_packet_ack', False))
        self.last_packet_ack_timeout_spin.setValue(self.initial_download_config.get('last_packet_ack_timeout', 1000))
        self.last_packet_ack_length_check.setChecked(self.initial_download_config.get('last_packet_ack_check_length', True))
        self.last_packet_ack_length_spin.setValue(self.initial_download_config.get('last_packet_ack_expected_length', 1))
        self.last_packet_ack_data_check.setChecked(self.initial_download_config.get('last_packet_ack_check_data', False))
        self.last_packet_ack_data_edit.setText(self.initial_download_config.get('last_packet_ack_expected_data', '0x06'))
        self.last_packet_ack_format_combo.setCurrentText(self.initial_download_config.get('last_packet_ack_data_format', 'HEX'))
        self.last_packet_ack_crc_check.setChecked(self.initial_download_config.get('last_packet_ack_check_crc', False))
        self.last_packet_ack_crc_type_combo.setCurrentText(self.initial_download_config.get('last_packet_ack_crc_type', 'CRC16-MODBUS'))

        last_packet_ack_mode_text = "全部满足 (AND)" if self.initial_download_config.get('last_packet_ack_check_mode', 'AND') == 'AND' else "任一满足 (OR)"
        self.last_packet_ack_mode_combo.setCurrentText(last_packet_ack_mode_text)

        # === 结尾字符串配置 ===
        self.send_end_string_check.setChecked(self.initial_download_config.get('send_end_string', False))
        self.end_string_edit.setText(self.initial_download_config.get('end_string', ''))

    def _refresh_ports(self):
        """刷新串口列表"""
        current_text = self.port_combo.currentText()
        self.port_combo.clear()

        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")

        # 恢复之前选择的端口
        if current_text:
            index = self.port_combo.findText(current_text, Qt.MatchStartsWith)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择固件文件",
            "",
            "Binary Files (*.bin);;All Files (*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            self.file_drop_label.setText(f"✓ 已选择文件\n{file_path}")

    def _on_file_dropped(self, file_path: str):
        """文件拖放回调"""
        self.file_path_edit.setText(file_path)

    def start_download(self):
        """开始下载"""
        # 验证配置
        firmware_path = self.file_path_edit.text().strip()
        if not firmware_path or not os.path.exists(firmware_path):
            QMessageBox.warning(self, "警告", "请选择有效的固件文件")
            return

        port_text = self.port_combo.currentText()
        if not port_text:
            QMessageBox.warning(self, "警告", "请选择串口")
            return

        # 提取串口号
        port = port_text.split(' ')[0]

        # 构建配置
        port_config = {
            'port': port,
            'baudrate': int(self.baudrate_combo.currentText()),
            'bytesize': int(self.bytesize_combo.currentText()),
            'parity': self._parse_parity(self.parity_combo.currentText()),
            'stopbits': float(self.stopbits_combo.currentText())
        }

        # 开始命令 ACK 配置
        start_ack_config = {
            'check_length': self.start_ack_length_check.isChecked(),
            'expected_length': self.start_ack_length_spin.value(),
            'check_data': self.start_ack_data_check.isChecked(),
            'expected_data': self.start_ack_data_edit.text(),
            'data_format': self.start_ack_format_combo.currentText(),
            'check_crc': False,  # 开始命令 ACK 不使用 CRC
            'check_mode': 'AND' if 'AND' in self.start_ack_mode_combo.currentText() else 'OR'
        }

        # 数据包 ACK 配置
        packet_ack_config = {
            'check_length': self.packet_ack_length_check.isChecked(),
            'expected_length': self.packet_ack_length_spin.value(),
            'check_data': self.packet_ack_data_check.isChecked(),
            'expected_data': self.packet_ack_data_edit.text(),
            'data_format': self.packet_ack_format_combo.currentText(),
            'check_crc': self.packet_ack_crc_check.isChecked(),
            'crc_type': self.packet_ack_crc_type_combo.currentText(),
            'check_mode': 'AND' if 'AND' in self.packet_ack_mode_combo.currentText() else 'OR'
        }

        # 末尾数据包 ACK 配置
        last_packet_ack_config = {
            'check_length': self.last_packet_ack_length_check.isChecked(),
            'expected_length': self.last_packet_ack_length_spin.value(),
            'check_data': self.last_packet_ack_data_check.isChecked(),
            'expected_data': self.last_packet_ack_data_edit.text(),
            'data_format': self.last_packet_ack_format_combo.currentText(),
            'check_crc': self.last_packet_ack_crc_check.isChecked(),
            'crc_type': self.last_packet_ack_crc_type_combo.currentText(),
            'check_mode': 'AND' if 'AND' in self.last_packet_ack_mode_combo.currentText() else 'OR'
        }

        download_config = {
            'start_command': self.start_cmd_edit.text(),
            'packet_size': self.packet_size_spin.value(),
            'wait_start_ack': self.start_ack_check.isChecked(),
            'start_ack_timeout': self.start_ack_timeout_spin.value(),
            'start_ack_config': start_ack_config,
            'wait_packet_ack': self.packet_ack_check.isChecked(),
            'packet_ack_timeout': self.packet_ack_timeout_spin.value(),
            'packet_ack_config': packet_ack_config,
            'wait_last_packet_ack': self.last_packet_ack_check.isChecked(),
            'last_packet_ack_timeout': self.last_packet_ack_timeout_spin.value(),
            'last_packet_ack_config': last_packet_ack_config,
            'add_packet_crc': self.packet_crc_check.isChecked(),
            'packet_crc_type': self.packet_crc_type_combo.currentText(),
            'send_end_string': self.send_end_string_check.isChecked(),
            'end_string': self.end_string_edit.text()
        }

        # 创建下载器
        self.downloader = FirmwareDownloader(port_config, download_config)

        # 打开串口
        success, message = self.downloader.open_port()
        if not success:
            QMessageBox.critical(self, "错误", message)
            return

        self.log_widget.append_log("INFO", message)

        # 重置进度
        self.progress_widget.reset()

        # 创建并启动下载线程
        self.download_thread = DownloadThread(self.downloader, firmware_path)
        self.download_thread.progress_signal.connect(self._on_progress)
        self.download_thread.log_signal.connect(self._on_log)
        self.download_thread.finished_signal.connect(self._on_finished)
        self.download_thread.speed_signal.connect(self.progress_widget.update_speed)
        self.download_thread.time_signal.connect(self.progress_widget.update_time)

        self.download_thread.start()

        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_download(self):
        """停止下载"""
        if self.downloader:
            self.downloader.stop()
            self.log_widget.append_log("WARNING", "正在停止下载...")

    def _on_progress(self, current: int, total: int, percentage: int):
        """进度更新回调"""
        self.progress_widget.update_progress(current, total, percentage)

    def _on_log(self, level: str, message: str):
        """日志更新回调"""
        self.log_widget.append_log(level, message)

    def _on_finished(self, success: bool, message: str):
        """下载完成回调"""
        # 关闭串口
        if self.downloader:
            self.downloader.close_port()

        # 更新按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # 显示结果
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "失败", message)

    def _parse_parity(self, parity_text: str) -> str:
        """解析校验位"""
        mapping = {
            'None': 'N',
            'Odd': 'O',
            'Even': 'E',
            'Mark': 'M',
            'Space': 'S'
        }
        return mapping.get(parity_text, 'N')

    def eventFilter(self, obj, event):
        """事件过滤器 - 禁用组合框滚轮"""
        from PyQt5.QtCore import QEvent
        if isinstance(obj, QComboBox) and event.type() == QEvent.Wheel:
            return True  # 忽略滚轮事件
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """关闭事件"""
        if self.download_thread and self.download_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认",
                "下载正在进行中，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.stop_download()
                self.download_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数 - 支持命令行参数"""
    app = QApplication(sys.argv)

    # 解析命令行参数
    args = sys.argv[1:]
    
    initial_file    = args[0]       if len(args) > 0 else "D:/BaiduSyncdisk/01_Code/Python/Bin2Hex/ZPX002_Test.bin"
    port            = args[1]       if len(args) > 1 else "COM15"
    baudrate        = int(args[2])  if len(args) > 2 else 115200

    dialog = FirmwareDownloaderDialog(
        initial_file=initial_file,
        port=port,
        baudrate=baudrate
    )
    dialog.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
