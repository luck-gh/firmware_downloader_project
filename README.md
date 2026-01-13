# 固件下载工具 (Firmware Downloader)

**版本**: 1.1 | **作者**: GHowe | **日期**: 2026-01-18

功能强大的串口固件下载工具，支持 GUI 界面、命令行调用和 Python 模块导入三种使用方式。

---

## 快速开始

### 方式 1: GUI 界面运行

```bash
python firmware_downloader_dialog.py
```

### 方式 2: 命令行调用

```bash
python firmware_downloader_dialog.py \
  --file firmware.bin \
  --port COM3 \
  --baudrate 115200 \
  --wait-packet-ack \
  --packet-ack-data "0x06"
```

### 方式 3: 作为 Python 模块导入

```python
from firmware_downloader_dialog import FirmwareDownloaderDialog

dialog = FirmwareDownloaderDialog(
    initial_file="firmware.bin",
    port="COM3",
    baudrate=115200,
    wait_packet_ack=True,
    packet_ack_check_data=True,
    packet_ack_expected_data="0x06"
)
dialog.show()
```

---

## 功能特性

### 核心功能

- ✅ **串口配置** - 支持自定义串口参数（波特率、数据位、停止位、校验位）
- ✅ **文件拖放** - 支持拖放 .bin 文件到界面
- ✅ **三阶段 ACK 配置** - 开始命令、数据包、末尾数据包独立配置
- ✅ **实时输入验证** - HEX/ASCII/DEC 格式实时验证，绿色/红色边框提示
- ✅ **转义字符支持** - 支持 `\r` `\n` `\t` `\0` `\xHH` `\\`
- ✅ **可调整界面布局** - 使用分割器自由调整配置区和日志区高度
- ✅ **滚轮操作优化** - 禁用配置控件的滚轮响应，防止误操作
- ✅ **日志过滤** - 可选择显示警告、信息、调试日志
- ✅ **应用图标** - 支持窗口图标和 EXE 图标

### 协议支持

- 发送开始命令（支持转义字符）
- 可配置数据包大小（1-4096 字节）
- 数据包 CRC 校验（CRC16-MODBUS/CCITT/XMODEM, CRC32）
- 三阶段 ACK 验证（开始命令/数据包/末尾数据包）
- 结尾字符串发送

### ACK 验证机制

每个 ACK 阶段支持:
- 长度判断
- 数据匹配（HEX/ASCII/DEC 格式）
- CRC 校验（仅数据包和末尾数据包）
- AND/OR 逻辑组合
- 可配置超时时间

---

## 安装

### 依赖安装

```bash
pip install PyQt5 pyserial
```

### 打包为独立可执行文件

```bash
# 安装打包工具
pip install pyinstaller

# 清理旧文件并打包
rm -rf build dist
pyinstaller firmware_downloader.spec

# 生成的 EXE 位于 dist/FirmwareDownloader.exe
```

**注意**:
- 打包后的 EXE 包含应用图标
- 如果图标未显示，请清除 Windows 图标缓存或重启资源管理器
- 详细打包配置请参考 [开发者笔记](docs/DEVELOPER_NOTES.md)

---

## 使用方式

### 1. GUI 界面使用

直接运行打开图形界面:

```bash
python firmware_downloader_dialog.py
```

或使用打包后的 EXE:

```bash
FirmwareDownloader.exe
```

### 2. 命令行参数使用

支持完整的命令行参数配置，适合批处理和自动化脚本。

**基本用法**:

```bash
python firmware_downloader_dialog.py \
  --file firmware.bin \
  --port COM3 \
  --baudrate 115200
```

**完整配置示例**:

```bash
python firmware_downloader_dialog.py \
  --file bootloader.bin \
  --port COM3 \
  --baudrate 115200 \
  --packet-size 512 \
  --start-command "START_FLASH\r\n" \
  --add-packet-crc \
  --packet-crc-type CRC16-MODBUS \
  --wait-packet-ack \
  --packet-ack-check-data \
  --packet-ack-expected-data "0x06" \
  --packet-ack-data-format HEX
```

**查看所有参数**:

```bash
python firmware_downloader_dialog.py --help
```

详细的命令行使用说明请参考 [命令行使用指南](docs/COMMAND_LINE_USAGE.md)

### 3. Python 模块导入使用

作为模块导入到其他 Python 项目中使用。

#### 基本导入

```python
from firmware_downloader_dialog import FirmwareDownloaderDialog
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

dialog = FirmwareDownloaderDialog(
    initial_file="firmware.bin",
    port="COM3",
    baudrate=115200
)
dialog.show()

sys.exit(app.exec_())
```

#### 完整参数配置

`FirmwareDownloaderDialog` 类的 `__init__` 方法支持以下参数:

##### 文件和串口配置

```python
dialog = FirmwareDownloaderDialog(
    # 文件路径
    initial_file="firmware.bin",

    # 串口配置
    port="COM3",
    baudrate=115200,
    bytesize=8,           # 数据位: 5/6/7/8
    parity="N",           # 校验位: N/O/E/M/S
    stopbits=1.0,         # 停止位: 1/1.5/2
)
```

##### 下载基本配置

```python
dialog = FirmwareDownloaderDialog(
    # ... 串口配置 ...

    # 下载配置
    packet_size=256,                    # 数据包大小(字节)
    start_command="download 0\\r\\n",   # 开始命令(支持转义字符)
    add_packet_crc=False,               # 是否追加数据包CRC
    packet_crc_type="CRC16-MODBUS",     # CRC类型
    send_end_string=False,              # 是否发送结尾字符串
    end_string="?\\r\\n",               # 结尾字符串
)
```

##### 开始命令 ACK 配置

```python
dialog = FirmwareDownloaderDialog(
    # ... 基本配置 ...

    # 开始命令 ACK
    wait_start_ack=True,
    start_ack_timeout=1000,                    # 超时(毫秒)
    start_ack_check_length=False,
    start_ack_expected_length=1,
    start_ack_check_data=True,
    start_ack_expected_data="download 0\\r\\nOK\\r\\n",
    start_ack_data_format="ASCII",             # HEX/ASCII/DEC
    start_ack_check_mode="AND",                # AND/OR
)
```

##### 数据包 ACK 配置

```python
dialog = FirmwareDownloaderDialog(
    # ... 基本配置 ...

    # 数据包 ACK
    wait_packet_ack=True,
    packet_ack_timeout=1000,
    packet_ack_check_length=False,
    packet_ack_expected_length=1,
    packet_ack_check_data=True,
    packet_ack_expected_data="OK\\r\\n",
    packet_ack_data_format="ASCII",
    packet_ack_check_crc=False,
    packet_ack_crc_type="CRC16-MODBUS",
    packet_ack_check_mode="AND",
)
```

##### 末尾数据包 ACK 配置

```python
dialog = FirmwareDownloaderDialog(
    # ... 基本配置 ...

    # 末尾数据包 ACK
    wait_last_packet_ack=True,
    last_packet_ack_timeout=5000,
    last_packet_ack_check_length=False,
    last_packet_ack_expected_length=1,
    last_packet_ack_check_data=True,
    last_packet_ack_expected_data="END\\r\\n",
    last_packet_ack_data_format="ASCII",
    last_packet_ack_check_crc=False,
    last_packet_ack_crc_type="CRC16-MODBUS",
    last_packet_ack_check_mode="AND",
)
```

#### 完整示例

```python
from firmware_downloader_dialog import FirmwareDownloaderDialog
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

# 创建对话框，配置三阶段 ACK
dialog = FirmwareDownloaderDialog(
    # 文件和串口
    initial_file="bootloader.bin",
    port="COM3",
    baudrate=460800,

    # 下载配置
    packet_size=512,
    start_command="START_FLASH\\r\\n",
    add_packet_crc=True,
    packet_crc_type="CRC16-MODBUS",

    # 开始命令 ACK
    wait_start_ack=True,
    start_ack_check_data=True,
    start_ack_expected_data="READY\\r\\n",
    start_ack_data_format="ASCII",

    # 数据包 ACK
    wait_packet_ack=True,
    packet_ack_check_data=True,
    packet_ack_expected_data="0x06",
    packet_ack_data_format="HEX",

    # 末尾数据包 ACK
    wait_last_packet_ack=True,
    last_packet_ack_check_data=True,
    last_packet_ack_expected_data="DONE\\r\\n",
    last_packet_ack_data_format="ASCII",
)

dialog.show()
sys.exit(app.exec_())
```

---

## API 参考

### FirmwareDownloaderDialog 类

```python
class FirmwareDownloaderDialog(QDialog):
    def __init__(
        self,
        parent=None,
        # 文件和串口配置
        initial_file: str = "",
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
    )
```

#### 参数类型说明

| 参数类型 | 可选值 | 说明 |
|---------|--------|------|
| **parity** | N, O, E, M, S | 校验位: None, Odd, Even, Mark, Space |
| **data_format** | HEX, ASCII, DEC | 数据格式: 十六进制, ASCII字符, 十进制 |
| **crc_type** | CRC16-MODBUS, CRC16-CCITT, CRC16-XMODEM, CRC32 | CRC 校验算法 |
| **check_mode** | AND, OR | 验证逻辑: 全部满足, 任一满足 |

#### 方法

```python
# 显示对话框
dialog.show()

# 模态显示(阻塞)
result = dialog.exec_()

# 开始下载
dialog.start_download()

# 停止下载
dialog.stop_download()
```

---

## 转义字符支持

在命令和数据中支持以下转义字符:

| 转义序列 | 说明 | 实际值 |
|---------|------|--------|
| `\r` | 回车符 | 0x0D |
| `\n` | 换行符 | 0x0A |
| `\t` | 制表符 | 0x09 |
| `\0` | 空字符 | 0x00 |
| `\xHH` | 十六进制字符 | 如 `\x1A` = 0x1A |
| `\\` | 反斜杠 | `\` |

**示例**:

```python
# ASCII 格式
start_command="DOWNLOAD\r\n"           # 带回车换行
packet_ack_expected_data="OK\r\n"     # 期望 OK 加回车换行

# HEX 格式
packet_ack_expected_data="0x06"       # 单字节 ACK
packet_ack_expected_data="0x06 0xAA" # 多字节

# DEC 格式
packet_ack_expected_data="6 170 187"  # 空格分隔的十进制数
```

---

## 下载流程

```
1. 打开串口
2. [可选] 发送开始命令
3. [可选] 等待开始命令 ACK
4. 循环发送数据包:
   ├─ 读取固件数据
   ├─ [可选] 追加 CRC
   ├─ 发送数据包
   ├─ [可选] 等待数据包 ACK
   └─ 更新进度
5. [可选] 发送末尾数据包
6. [可选] 等待末尾数据包 ACK
7. [可选] 发送结尾字符串
8. 关闭串口
```

---

## ACK 验证逻辑

### AND 模式（全部满足）

所有启用的检查项都必须通过:

```
✓ 长度检查 (期望:1, 实际:1)
✓ 数据匹配 (收到:06)
✓ CRC 校验
→ 结果: 通过
```

### OR 模式（任一满足）

任意一个检查项通过即可:

```
✗ 长度检查 (期望:2, 实际:1)
✓ 数据匹配 (收到:06)
✗ CRC 校验
→ 结果: 通过（因为数据匹配成功）
```

---

## CRC 类型说明

| CRC 类型 | 长度 | 说明 | 常见应用 |
|----------|------|------|----------|
| CRC16-MODBUS | 2 字节 | 初始值 0xFFFF，多项式 0xA001，小端 | Modbus RTU 协议 |
| CRC16-CCITT | 2 字节 | 初始值 0xFFFF，多项式 0x1021，大端 | XMODEM, Bluetooth |
| CRC16-XMODEM | 2 字节 | 初始值 0x0000，多项式 0x1021，大端 | XMODEM 协议 |
| CRC32 | 4 字节 | 标准 CRC32，小端 | ZIP, PNG, Ethernet |

---

## 集成到其他项目

### 方式 1: 直接复制模块

将整个项目目录复制到目标项目中:

```
your_project/
├── firmware_downloader_project/
│   ├── firmware_downloader_dialog.py
│   ├── core/
│   ├── widgets/
│   └── resources/
└── your_main.py
```

然后导入使用:

```python
from firmware_downloader_project.firmware_downloader_dialog import FirmwareDownloaderDialog
```

### 方式 2: 使用打包的 EXE

通过 subprocess 调用打包后的 EXE:

```python
import subprocess

subprocess.run([
    "FirmwareDownloader.exe",
    "--file", "firmware.bin",
    "--port", "COM3",
    "--wait-packet-ack",
    "--packet-ack-data", "0x06"
])
```

### 方式 3: 作为 Git 子模块

```bash
cd your_project
git submodule add <repository_url> firmware_downloader
```

---

## 常见问题

### Q: 串口打开失败

**原因**:
- 串口被其他程序占用
- 串口号不存在
- 权限不足

**解决**:
1. 关闭其他串口工具
2. 检查设备管理器中的串口号
3. 以管理员权限运行

### Q: ACK 超时

**原因**:
- 设备未响应
- 超时时间设置过短
- ACK 格式配置错误

**解决**:
1. 增加超时时间
2. 使用串口调试工具确认设备响应格式
3. 检查 ACK 数据格式配置

### Q: ACK 验证失败

**原因**:
- 预期数据与实际接收不符
- 数据格式配置错误
- 多个检查条件使用 AND 模式过于严格

**解决**:
1. 查看日志中的实际接收数据
2. 调整预期数据和格式
3. 尝试使用 OR 模式

### Q: 下载速度慢

**原因**:
- 数据包过小
- 波特率设置过低
- 每包等待 ACK 增加延迟

**解决**:
1. 增大数据包大小（256→512→1024）
2. 提高波特率
3. 如设备支持，禁用 ACK 等待

---

## 版本历史

### V1.1 (2026-01-18) - UI 优化版

**界面改进**:
- ✅ 添加垂直分割器，支持鼠标拖动调整配置区和日志区高度
- ✅ 缩小文件选择拖拽框高度，优化空间利用
- ✅ 禁用所有配置控件的滚轮响应，防止误操作
- ✅ 添加应用图标支持（窗口图标 + EXE 图标）

**功能增强**:
- ✅ 完整的命令行参数支持（40+ 参数）
- ✅ 新增命令行使用文档 COMMAND_LINE_USAGE.md

**技术改进**:
- ✅ 使用 QSplitter 实现界面可调整布局
- ✅ 统一事件过滤器处理滚轮事件
- ✅ 新增 `widgets/utils.py` 工具模块
- ✅ 改进资源文件路径处理

### V1.0 (2026-01-14) - 首次发布

- ✅ 分离的 ACK 配置（开始命令/数据包/末尾数据包）
- ✅ 实时输入验证（HEX/ASCII/DEC）
- ✅ 转义字符支持
- ✅ 日志过滤功能
- ✅ 代码优化（减少 ~40% 重复）

---

## 相关文档

- [命令行使用指南](docs/COMMAND_LINE_USAGE.md) - 命令行参数详细说明和示例
- [开发者笔记](docs/DEVELOPER_NOTES.md) - 代码结构、维护要点和开发指南

---

## 许可证

MIT License

---

**作者**: GHowe
**项目**: firmware_downloader_project
**联系**: <844396800@qq.com>
