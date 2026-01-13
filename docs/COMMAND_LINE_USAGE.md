# 命令行参数使用指南

固件下载工具支持完整的命令行参数配置，与 GUI 界面功能一致。

## 快速开始

### 查看所有可用参数
```bash
python firmware_downloader_dialog.py --help
```

### 基本使用
```bash
# 最简单的使用方式（只指定文件和串口）
python firmware_downloader_dialog.py --file firmware.bin --port COM3

# 使用短参数
python firmware_downloader_dialog.py -f firmware.bin -p COM3 -b 115200
```

## 完整参数列表

### 文件和串口配置

| 参数 | 短参数 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--file` | `-f` | str | "" | 固件文件路径 (.bin) |
| `--port` | `-p` | str | "" | 串口号 (如 COM3, /dev/ttyUSB0) |
| `--baudrate` | `-b` | int | 115200 | 波特率 |
| `--bytesize` | - | int | 8 | 数据位 (5/6/7/8) |
| `--parity` | - | str | N | 校验位 (N/O/E/M/S) |
| `--stopbits` | - | float | 1.0 | 停止位 (1/1.5/2) |

### 下载基本配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--packet-size` | int | 256 | 数据包大小 (字节) |
| `--start-command` | str | "download 0\r\n" | 开始命令 (支持转义字符) |
| `--add-packet-crc` | flag | False | 在数据包后追加 CRC |
| `--packet-crc-type` | str | CRC16-MODBUS | CRC 类型 |

### 开始命令 ACK 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--wait-start-ack` | flag | False | 等待开始命令 ACK |
| `--start-ack-timeout` | int | 1000 | 超时时间 (毫秒) |
| `--start-ack-check-length` | flag | False | 检查 ACK 长度 |
| `--start-ack-expected-length` | int | 1 | 预期长度 |
| `--start-ack-check-data` | flag | False | 检查 ACK 数据 |
| `--start-ack-expected-data` | str | "download 0\r\nOK\r\n" | 预期数据 |
| `--start-ack-data-format` | str | ASCII | 数据格式 (HEX/ASCII/DEC) |
| `--start-ack-check-mode` | str | AND | 检查模式 (AND/OR) |

### 数据包 ACK 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--wait-packet-ack` | flag | False | 等待数据包 ACK |
| `--packet-ack-timeout` | int | 1000 | 超时时间 (毫秒) |
| `--packet-ack-check-length` | flag | False | 检查 ACK 长度 |
| `--packet-ack-expected-length` | int | 1 | 预期长度 |
| `--packet-ack-check-data` | flag | False | 检查 ACK 数据 |
| `--packet-ack-expected-data` | str | "OK\r\n" | 预期数据 |
| `--packet-ack-data-format` | str | ASCII | 数据格式 (HEX/ASCII/DEC) |
| `--packet-ack-check-crc` | flag | False | 检查 ACK CRC |
| `--packet-ack-crc-type` | str | CRC16-MODBUS | CRC 类型 |
| `--packet-ack-check-mode` | str | AND | 检查模式 (AND/OR) |

### 末尾数据包 ACK 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--wait-last-packet-ack` | flag | False | 等待末尾数据包 ACK |
| `--last-packet-ack-timeout` | int | 5000 | 超时时间 (毫秒) |
| `--last-packet-ack-check-length` | flag | False | 检查 ACK 长度 |
| `--last-packet-ack-expected-length` | int | 1 | 预期长度 |
| `--last-packet-ack-check-data` | flag | False | 检查 ACK 数据 |
| `--last-packet-ack-expected-data` | str | "END\r\n" | 预期数据 |
| `--last-packet-ack-data-format` | str | ASCII | 数据格式 (HEX/ASCII/DEC) |
| `--last-packet-ack-check-crc` | flag | False | 检查 ACK CRC |
| `--last-packet-ack-crc-type` | str | CRC16-MODBUS | CRC 类型 |
| `--last-packet-ack-check-mode` | str | AND | 检查模式 (AND/OR) |

### 结尾字符串配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--send-end-string` | flag | False | 发送结尾字符串 |
| `--end-string` | str | "?\r\n" | 结尾字符串 |

## 使用示例

### 示例 1: 基本下载（无 ACK）

```bash
python firmware_downloader_dialog.py \
  --file firmware.bin \
  --port COM3 \
  --baudrate 115200 \
  --packet-size 256
```

### 示例 2: 等待简单 ACK (0x06)

```bash
python firmware_downloader_dialog.py \
  --file firmware.bin \
  --port COM5 \
  --baudrate 460800 \
  --wait-packet-ack \
  --packet-ack-check-data \
  --packet-ack-expected-data "0x06" \
  --packet-ack-data-format HEX
```

### 示例 3: 完整配置（数据包 CRC + ACK 验证）

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
  --packet-ack-timeout 2000 \
  --packet-ack-check-length \
  --packet-ack-expected-length 3 \
  --packet-ack-check-data \
  --packet-ack-expected-data "0x06" \
  --packet-ack-data-format HEX \
  --packet-ack-check-crc \
  --packet-ack-crc-type CRC16-MODBUS \
  --packet-ack-check-mode AND
```

### 示例 4: 使用串口配置

```bash
python firmware_downloader_dialog.py \
  --file firmware.bin \
  --port COM3 \
  --baudrate 921600 \
  --bytesize 8 \
  --parity N \
  --stopbits 1 \
  --packet-size 1024
```

### 示例 5: 三阶段 ACK（开始 + 数据包 + 末尾）

```bash
python firmware_downloader_dialog.py \
  --file firmware.bin \
  --port COM3 \
  --start-command "DOWNLOAD\r\n" \
  --wait-start-ack \
  --start-ack-check-data \
  --start-ack-expected-data "READY\r\n" \
  --start-ack-data-format ASCII \
  --wait-packet-ack \
  --packet-ack-check-data \
  --packet-ack-expected-data "0x06" \
  --packet-ack-data-format HEX \
  --wait-last-packet-ack \
  --last-packet-ack-check-data \
  --last-packet-ack-expected-data "DONE\r\n" \
  --last-packet-ack-data-format ASCII
```

## 参数类型说明

### Flag 类型参数

Flag 参数不需要值，出现即表示启用:

```bash
# 启用数据包 CRC
python firmware_downloader_dialog.py --add-packet-crc

# 启用 ACK 等待
python firmware_downloader_dialog.py --wait-packet-ack
```

### 选择类型参数

某些参数只接受特定值:

```bash
# CRC 类型: CRC16-MODBUS, CRC16-CCITT, CRC16-XMODEM, CRC32
--packet-crc-type CRC16-MODBUS

# 数据格式: HEX, ASCII, DEC
--packet-ack-data-format HEX

# 校验位: N, O, E, M, S
--parity N

# 检查模式: AND, OR
--packet-ack-check-mode AND
```

## 转义字符支持

在命令行中使用转义字符:

```bash
# ASCII 格式支持转义字符
--start-command "DOWNLOAD\r\n"
--packet-ack-expected-data "OK\r\n"

# HEX 格式使用 0x 前缀
--packet-ack-expected-data "0x06"
--packet-ack-expected-data "0x06 0xAA 0xBB"

# DEC 格式使用空格分隔
--packet-ack-expected-data "6 170 187"
```

## Windows 批处理脚本示例

创建 `.bat` 文件快速启动:

```batch
@echo off
REM download_firmware.bat

python firmware_downloader_dialog.py ^
  --file "D:\firmware\app.bin" ^
  --port COM3 ^
  --baudrate 115200 ^
  --packet-size 256 ^
  --wait-packet-ack ^
  --packet-ack-check-data ^
  --packet-ack-expected-data "0x06" ^
  --packet-ack-data-format HEX

pause
```

**注意**: Windows 批处理中使用 `^` 作为续行符。

## Linux/Mac Shell 脚本示例

创建 `.sh` 文件:

```bash
#!/bin/bash
# download_firmware.sh

python3 firmware_downloader_dialog.py \
  --file "/path/to/firmware.bin" \
  --port /dev/ttyUSB0 \
  --baudrate 115200 \
  --packet-size 256 \
  --wait-packet-ack \
  --packet-ack-check-data \
  --packet-ack-expected-data "0x06" \
  --packet-ack-data-format HEX
```

赋予执行权限并运行:

```bash
chmod +x download_firmware.sh
./download_firmware.sh
```

## 配置文件（JSON）示例

虽然不直接支持配置文件，但可以通过脚本读取 JSON 配置:

**config.json**:
```json
{
  "file": "firmware.bin",
  "port": "COM3",
  "baudrate": 115200,
  "packet_size": 256,
  "wait_packet_ack": true,
  "packet_ack_check_data": true,
  "packet_ack_expected_data": "0x06",
  "packet_ack_data_format": "HEX"
}
```

**load_config.py**:
```python
import json
import subprocess

with open('config.json', 'r') as f:
    config = json.load(f)

cmd = ['python', 'firmware_downloader_dialog.py']
for key, value in config.items():
    param = f"--{key.replace('_', '-')}"
    if isinstance(value, bool):
        if value:
            cmd.append(param)
    else:
        cmd.extend([param, str(value)])

subprocess.run(cmd)
```

## 常见问题

### Q: 如何不显示 GUI 界面直接下载？

A: 当前版本总是显示 GUI 界面。如需纯命令行模式，需要使用 `FirmwareDownloader` 类而非 `FirmwareDownloaderDialog`。

### Q: 参数太多，如何简化？

A: 使用批处理/Shell 脚本保存常用配置，或创建 Python 包装脚本读取配置文件。

### Q: 如何查看实际使用的参数值？

A: 启动后在 GUI 界面可以看到所有配置已经被应用。

---

**提示**: 所有参数都是可选的，未指定的参数将使用默认值。
