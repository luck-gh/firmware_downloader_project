# 固件下载工具 - 开发者笔记

**版本**: 1.1 | **更新日期**: 2026-01-18

本文档面向开发者和维护人员，记录代码结构、设计要点、维护注意事项等。

---

## 项目结构

```
firmware_downloader_project/
├── firmware_downloader_dialog.py  # 主对话框（GUI + 命令行入口）
├── core/
│   ├── __init__.py
│   ├── downloader.py             # 核心下载器
│   ├── protocol.py               # 协议处理器
│   ├── ack_validator.py          # ACK 验证器
│   └── crc_calculator.py         # CRC 计算器
├── widgets/
│   ├── __init__.py
│   ├── widgets.py                # 自定义控件（FileDropLabel, LogWidget, etc.）
│   └── utils.py                  # 工具函数（resource_path）
├── resources/
│   └── HOWE_LOGO.ico             # 应用图标
├── docs/
│   ├── COMMAND_LINE_USAGE.md     # 命令行使用指南
│   └── DEVELOPER_NOTES.md        # 本文档
├── firmware_downloader.spec      # PyInstaller 打包配置
└── README.md                     # 用户文档
```

---

## 核心模块说明

### 1. firmware_downloader_dialog.py

**职责**:
- GUI 界面（PyQt5）
- 命令行参数解析（argparse）
- 用户交互逻辑

**关键类**:

#### `DownloadThread(QThread)`
- 下载线程，避免阻塞 GUI
- 发送信号: progress_signal, log_signal, finished_signal, speed_signal, time_signal

#### `FirmwareDownloaderDialog(QDialog)`
- 主对话框类
- 支持 40+ 初始化参数
- 三阶段 ACK 配置
- 实时日志和进度显示

**关键方法**:
- `init_ui()` - 初始化界面，使用 QSplitter 分割布局
- `_create_ack_config_section()` - 创建可折叠的 ACK 配置区域（代码复用）
- `apply_initial_config()` - 应用初始参数到 UI 控件
- `eventFilter()` - 禁用 QComboBox 和 QSpinBox 的滚轮事件

### 2. core/downloader.py

**职责**:
- 串口通信
- 固件文件读取
- 下载流程控制

**关键类**:

#### `FirmwareDownloader`
```python
def __init__(self, port_config: dict, download_config: dict)
def open_port() -> tuple[bool, str]
def close_port()
def download(firmware_path: str, progress_callback, log_callback) -> tuple[bool, str]
```

**下载流程**:
1. 打开串口
2. 发送开始命令 + 等待 ACK（可选）
3. 循环发送数据包 + 等待 ACK（可选）
4. 发送末尾数据包 + 等待 ACK（可选）
5. 发送结尾字符串（可选）
6. 关闭串口

### 3. core/protocol.py

**职责**:
- 转义字符解析
- 数据格式转换（HEX/ASCII/DEC）
- 协议处理

**关键类**:

#### `ProtocolHandler`
```python
@staticmethod
def parse_escape_string(s: str) -> bytes
@staticmethod
def parse_data_to_bytes(data: str, format: str) -> bytes
@staticmethod
def bytes_to_hex_string(data: bytes) -> str
```

**转义字符支持**:
- `\r` → 0x0D
- `\n` → 0x0A
- `\t` → 0x09
- `\0` → 0x00
- `\xHH` → 0xHH
- `\\` → `\`

### 4. core/ack_validator.py

**职责**:
- ACK 数据验证
- 支持长度、数据、CRC 三种校验
- 支持 AND/OR 逻辑

**关键类**:

#### `AckValidator`
```python
def __init__(self, config: dict)
def validate(self, data: bytes) -> tuple[bool, str]
```

**验证逻辑**:
- AND 模式: 所有启用的检查都必须通过
- OR 模式: 任一检查通过即可

### 5. core/crc_calculator.py

**职责**:
- 计算各种 CRC 校验值

**关键类**:

#### `CRCCalculator`
```python
@staticmethod
def calculate(data: bytes, crc_type: str) -> bytes
```

**支持的 CRC 类型**:
- CRC16-MODBUS: Modbus RTU 协议
- CRC16-CCITT: XMODEM, Bluetooth
- CRC16-XMODEM: XMODEM 协议
- CRC32: ZIP, PNG, Ethernet

### 6. widgets/widgets.py

**职责**:
- 自定义 UI 控件

**关键类**:

#### `FileDropLabel(QLabel)`
- 支持拖放 .bin 文件
- 发送 file_dropped 信号

#### `LogWidget(QTextEdit)`
- 带颜色的日志显示
- 支持日志级别过滤
- 自动滚动到底部

#### `ProgressWidget(QWidget)`
- 进度条
- 速度显示
- 时间显示

#### `ValidatedLineEdit(QLineEdit)`
- 实时输入验证
- 支持 HEX/ASCII/DEC 格式
- 绿色/红色边框提示

### 7. widgets/utils.py

**职责**:
- 工具函数

**关键函数**:

#### `resource_path(relative_path: str) -> str`
- 处理资源文件路径
- 支持开发环境和 PyInstaller 打包环境
- 使用 `sys._MEIPASS` 检测打包状态

---

## 设计要点

### 1. 代码复用

**V1.0 优化**: 将三个 ACK 配置区域合并为一个通用方法 `_create_ack_config_section()`，减少约 40% 重复代码。

**关键参数**:
- `prefix`: 控件名称前缀（"start" / "packet" / "last_packet"）
- `title`: 显示标题
- `enable_crc`: 是否启用 CRC 校验选项
- `default_timeout`: 默认超时时间

### 2. 可折叠配置区域

**实现方式**:
- 使用 QPushButton 作为折叠/展开按钮
- 使用 `setVisible()` 控制配置区域显示
- 使用 `updateGeometry()` 强制更新布局

**好处**:
- 减少界面初始高度
- 提高配置区域可读性
- 用户可按需展开

### 3. 事件过滤器统一处理

**V1.1 改进**: 使用统一的 `eventFilter()` 处理所有 QComboBox 和 QSpinBox 的滚轮事件。

```python
def eventFilter(self, obj, event):
    from PyQt5.QtCore import QEvent
    if (isinstance(obj, (QComboBox, QSpinBox)) and event.type() == QEvent.Wheel):
        return True  # 忽略滚轮事件
    return super().eventFilter(obj, event)
```

**注意**: 必须为每个控件调用 `installEventFilter(self)`。

### 4. QSplitter 分割布局

**V1.1 新增**: 使用 QSplitter 实现可调整布局。

```python
main_splitter = QSplitter(Qt.Vertical)
main_splitter.addWidget(top_widget)      # 配置区
main_splitter.addWidget(bottom_widget)   # 日志区
main_splitter.setSizes([400, 200])       # 初始比例
```

### 5. 命令行参数系统

**V1.1 新增**: 使用 argparse 实现完整的命令行支持。

**要点**:
- 使用 `action='store_true'` 处理布尔参数
- 使用 `choices=[]` 限制参数值
- 使用 `RawDescriptionHelpFormatter` 保留示例格式
- 参数名使用连字符（`--packet-size`）

---

## PyInstaller 打包

### 1. 打包配置 (firmware_downloader.spec)

**关键配置**:

```python
# 定义图标路径
icon_path = os.path.join(spec_dir, 'resources', 'HOWE_LOGO.ico')

# 数据文件
datas=[
    (os.path.join(spec_dir, 'resources'), 'resources'),
],

# 隐藏导入
hiddenimports=[
    'firmware_downloader_project',
    'firmware_downloader_project.core',
    'firmware_downloader_project.widgets',
    # ...
],

# 图标设置
icon=icon_path,

# 不显示控制台
console=False,
```

### 2. 资源文件路径处理

**问题**: PyInstaller 打包后，资源文件路径会改变。

**解决**: 使用 `widgets/utils.py` 中的 `resource_path()` 函数。

```python
def resource_path(relative_path):
    """获取资源文件的绝对路径（支持打包和开发环境）"""
    try:
        # PyInstaller 创建临时文件夹，路径存储在 _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
```

**使用**:
```python
icon_path = resource_path("resources/HOWE_LOGO.ico")
if os.path.exists(icon_path):
    self.setWindowIcon(QIcon(icon_path))
```

### 3. 图标缓存问题

**问题**: Windows 会缓存 EXE 图标，重新打包后图标可能不更新。

**解决方案**:

```bash
# 方案 1: 清除图标缓存
ie4uinit.exe -show
ie4uinit.exe -ClearIconCache
taskkill /f /im explorer.exe
start explorer.exe

# 方案 2: 重启电脑（最彻底）

# 方案 3: 将 EXE 移到其他位置
```

### 4. 打包命令

```bash
# 清理旧文件
rm -rf build dist

# 使用 spec 文件打包
pyinstaller firmware_downloader.spec

# 验证图标是否嵌入（可选）
python check_icon.py dist/FirmwareDownloader.exe
```

---

## 维护要点

### 1. 添加新的 ACK 阶段

如果需要添加新的 ACK 验证阶段（例如"重启命令 ACK"）:

1. 在 `__init__()` 中添加参数
2. 在 `initial_download_config` 中添加配置
3. 在 `_create_config_group()` 中调用 `_create_ack_config_section()`
4. 在 `apply_initial_config()` 中应用初始值
5. 在 `start_download()` 中读取配置并传递给 downloader
6. 在 `main()` 中添加命令行参数
7. 更新文档

### 2. 添加新的 CRC 类型

在 `core/crc_calculator.py` 中:

```python
@staticmethod
def calculate(data: bytes, crc_type: str) -> bytes:
    if crc_type == "NEW-CRC":
        # 实现新的 CRC 算法
        return new_crc_bytes
    # ... 现有代码
```

同时更新:
- UI 中的下拉框选项
- 命令行参数的 choices
- 文档

### 3. 修改界面布局

**注意事项**:
- 使用 QSplitter 确保用户可调整
- 为控件添加 `installEventFilter(self)` 禁用滚轮
- 保持代码复用（使用通用方法）

### 4. 调试技巧

**查看实时日志**:
```python
# 在 downloader.py 中添加
print(f"DEBUG: 发送数据: {data.hex()}")
print(f"DEBUG: 接收ACK: {ack.hex()}")
```

**验证转义字符**:
```python
from core.protocol import ProtocolHandler
result = ProtocolHandler.parse_escape_string("test\\r\\n")
print(result)  # b'test\r\n'
```

**测试 ACK 验证**:
```python
from core.ack_validator import AckValidator

config = {
    'check_data': True,
    'expected_data': '0x06',
    'data_format': 'HEX',
    'check_mode': 'AND'
}

validator = AckValidator(config)
success, msg = validator.validate(b'\x06')
print(success, msg)
```

---

## 已知问题和限制

### 1. 串口独占

**问题**: 串口只能被一个程序同时使用。

**影响**: 如果其他程序（如串口调试助手）已打开串口，本工具无法打开。

**解决**: 关闭其他串口工具后再使用。

### 2. 大文件内存占用

**问题**: 当前实现会将整个固件文件读入内存。

**影响**: 对于超大文件（>100MB）可能占用较多内存。

**优化方向**: 改为流式读取（分块读取文件）。

### 3. Windows 图标缓存

**问题**: 重新打包后 EXE 图标可能不更新。

**原因**: Windows 文件资源管理器缓存图标。

**解决**: 见 "PyInstaller 打包 > 图标缓存问题" 章节。

### 4. 命令行中文显示

**问题**: Windows cmd 中中文可能显示乱码。

**解决**:
```cmd
chcp 65001  # 切换到 UTF-8 编码
python firmware_downloader_dialog.py --help
```

---

## 测试清单

### 功能测试

- [ ] GUI 界面正常打开
- [ ] 文件拖放功能
- [ ] 串口列表刷新
- [ ] 开始/停止下载
- [ ] 三阶段 ACK 配置
- [ ] 日志过滤功能
- [ ] 进度显示和速度统计
- [ ] 窗口图标显示

### 命令行测试

- [ ] `--help` 显示帮助
- [ ] 基本参数（--file, --port, --baudrate）
- [ ] ACK 配置参数
- [ ] 转义字符处理
- [ ] 错误参数提示

### 打包测试

- [ ] EXE 文件生成
- [ ] EXE 图标正确显示
- [ ] 双击运行正常
- [ ] 资源文件正确加载
- [ ] 命令行参数支持

### 协议测试

- [ ] 转义字符解析
- [ ] HEX 格式数据解析
- [ ] ASCII 格式数据解析
- [ ] DEC 格式数据解析
- [ ] CRC 计算正确性
- [ ] ACK 验证逻辑（AND/OR）

---

## 性能优化建议

### 1. 提高下载速度

- 增大数据包大小（256 → 1024）
- 提高波特率（115200 → 921600）
- 减少 ACK 等待（如设备支持）

### 2. 降低内存占用

- 改为流式读取文件
- 限制日志缓冲区大小

### 3. 改进 UI 响应性

- 已使用 QThread 处理下载任务
- 避免在主线程执行耗时操作

---

## 代码风格规范

### 1. 命名约定

- 类名: `CamelCase` (如 `FirmwareDownloader`)
- 方法名: `snake_case` (如 `start_download`)
- 私有方法: `_snake_case` (如 `_create_port_group`)
- 常量: `UPPER_CASE` (如 `DEFAULT_BAUDRATE`)

### 2. 文档字符串

```python
def example_method(self, param1: str, param2: int) -> bool:
    """
    方法简短描述

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        返回值说明
    """
    pass
```

### 3. 类型注解

尽可能使用类型注解:

```python
def download(self, path: str) -> tuple[bool, str]:
    pass
```

---

## Git 提交规范

### 提交信息格式

```
<type>: <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat: 添加命令行参数支持

- 使用 argparse 解析 40+ 参数
- 支持所有 GUI 功能
- 添加 COMMAND_LINE_USAGE.md 文档
```

---

## 相关资源

### 文档

- [README.md](../README.md) - 用户文档
- [COMMAND_LINE_USAGE.md](COMMAND_LINE_USAGE.md) - 命令行使用指南

### 依赖库文档

- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [PySerial Documentation](https://pythonhosted.org/pyserial/)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [argparse Documentation](https://docs.python.org/3/library/argparse.html)

### 工具

- PyInstaller: 打包工具
- pefile: 查看 EXE 资源（可选）

---

**维护者**: GHowe
**最后更新**: 2026-01-18
