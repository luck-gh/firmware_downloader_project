# 固件下载工具 (Firmware Downloader)

**版本**: 2.0 | **作者**: GuoHowe | **日期**: 2026-01-14

通过串口下载二进制固件文件到设备的 PyQt5 工具。

## 功能特性

### 核心功能
- ✅ **串口配置** - 支持自定义串口参数（波特率、数据位、停止位、校验位）
- ✅ **文件拖放** - 支持拖放 .bin 文件到界面
- ✅ **分离的 ACK 配置** ⭐ - 开始命令、数据包、末尾数据包独立配置
- ✅ **实时输入验证** ⭐ - HEX/ASCII/DEC 格式实时验证，绿色/红色边框提示
- ✅ **转义字符支持** ⭐ - 支持 `\r` `\n` `\t` `\0` `\xHH` `\\`
- ✅ **日志过滤** - 可选择显示警告、信息、调试日志

### 协议支持
- 发送开始命令（支持转义字符）
- 可配置数据包大小（1-4096字节）
- 数据包 CRC 校验（CRC16-MODBUS/CCITT/XMODEM, CRC32）
- 结尾字符串发送

### ACK 验证机制
- 长度判断
- 数据匹配判断（HEX/ASCII/DEC 格式）
- CRC 校验判断
- 支持 AND/OR 逻辑组合
- 可配置超时时间

### 实时反馈
- 进度条显示
- 下载速度统计
- 详细日志输出（可过滤）
- 串口状态监控

## 安装依赖

```bash
pip install PyQt5 pyserial
```

## 使用方法

### 1. 独立运行

```bash
python firmware_downloader_dialog.py
```

### 2. 指定初始文件

```bash
python firmware_downloader_dialog.py firmware.bin
```

### 3. 指定串口和波特率

```bash
python firmware_downloader_dialog.py firmware.bin COM3 115200
```

### 4. 作为模块导入

```python
from firmware_downloader_project.firmware_downloader_dialog import FirmwareDownloaderDialog

dialog = FirmwareDownloaderDialog(
    initial_file="firmware.bin",
    port="COM3",
    baudrate=115200,
    packet_size=256,
    wait_ack=True,
    ack_check_length=True,
    ack_expected_length=1,
    ack_check_data=True,
    ack_expected_data="0x06",
    ack_data_format="HEX"
)
dialog.exec_()
```

## 配置参数说明

### 串口配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| port | str | "" | 串口号 (如 COM3) |
| baudrate | int | 115200 | 波特率 |
| bytesize | int | 8 | 数据位 (5/6/7/8) |
| parity | str | "N" | 校验位 (N/O/E/M/S) |
| stopbits | float | 1 | 停止位 (1/1.5/2) |

### 下载配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| start_command | str | "START_DOWNLOAD" | 开始命令 |
| packet_size | int | 256 | 数据包大小 (字节) |
| timeout | int | 1000 | 超时时间 (毫秒) |
| add_packet_crc | bool | False | 是否在数据包后追加 CRC |
| packet_crc_type | str | "CRC16-MODBUS" | 数据包 CRC 类型 |

### ACK 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| wait_ack | bool | False | 是否等待 ACK |
| ack_check_length | bool | True | 检查 ACK 长度 |
| ack_expected_length | int | 1 | 预期 ACK 长度 |
| ack_check_data | bool | False | 检查 ACK 数据 |
| ack_expected_data | str | "0x06" | 预期 ACK 数据 |
| ack_data_format | str | "HEX" | ACK 数据格式 (HEX/ASCII/DEC) |
| ack_check_crc | bool | False | 检查 ACK 的 CRC |
| ack_crc_type | str | "CRC16-MODBUS" | ACK CRC 类型 |
| ack_check_mode | str | "AND" | 判断逻辑 (AND/OR) |

## 使用示例

### 示例 1: 简单下载（无 ACK）

```python
dialog = FirmwareDownloaderDialog(
    initial_file="firmware.bin",
    port="COM3",
    baudrate=115200,
    packet_size=256,
    start_command="DOWNLOAD",
    wait_ack=False
)
```

### 示例 2: 等待固定 ACK (0x06)

```python
dialog = FirmwareDownloaderDialog(
    initial_file="firmware.bin",
    port="COM3",
    baudrate=115200,
    packet_size=256,
    wait_ack=True,
    ack_check_data=True,
    ack_expected_data="0x06",
    ack_data_format="HEX",
    ack_check_mode="AND"
)
```

### 示例 3: 数据包带 CRC + ACK 长度判断

```python
dialog = FirmwareDownloaderDialog(
    initial_file="firmware.bin",
    port="COM3",
    baudrate=115200,
    packet_size=512,
    add_packet_crc=True,
    packet_crc_type="CRC16-MODBUS",
    wait_ack=True,
    ack_check_length=True,
    ack_expected_length=1,
    ack_check_mode="AND"
)
```

### 示例 4: 完整 ACK 验证（长度 + 数据 + CRC）

```python
dialog = FirmwareDownloaderDialog(
    initial_file="bootloader.bin",
    port="COM5",
    baudrate=460800,
    packet_size=1024,
    start_command="START_FLASH",
    add_packet_crc=True,
    packet_crc_type="CRC16-CCITT",
    wait_ack=True,
    ack_check_length=True,
    ack_expected_length=3,  # 1字节数据 + 2字节CRC
    ack_check_data=True,
    ack_expected_data="0x06",
    ack_check_crc=True,
    ack_crc_type="CRC16-MODBUS",
    ack_check_mode="AND"  # 所有条件都要满足
)
```

## 下载流程

```
1. 打开串口
2. [可选] 发送开始命令
3. [可选] 等待开始命令的 ACK
4. 循环发送数据包:
   ├─ 读取固件数据
   ├─ [可选] 追加 CRC
   ├─ 发送数据包
   ├─ [可选] 等待 ACK
   └─ 更新进度
5. 下载完成
6. 关闭串口
```

## ACK 验证逻辑

### AND 模式（全部满足）
所有启用的检查项都必须通过：

```
✓ 长度检查 (期望:1, 实际:1)
✓ 数据匹配 (收到:06)
✓ CRC 校验
→ 结果: 通过
```

### OR 模式（任一满足）
任意一个检查项通过即可：

```
✗ 长度检查 (期望:2, 实际:1)
✓ 数据匹配 (收到:06)
✗ CRC 校验
→ 结果: 通过（因为数据匹配成功）
```

## CRC 类型说明

| CRC 类型 | 长度 | 说明 | 常见应用 |
|----------|------|------|----------|
| CRC16-MODBUS | 2 字节 | 初始值 0xFFFF，多项式 0xA001，小端 | Modbus RTU 协议 |
| CRC16-CCITT | 2 字节 | 初始值 0xFFFF，多项式 0x1021，大端 | XMODEM, Bluetooth |
| CRC16-XMODEM | 2 字节 | 初始值 0x0000，多项式 0x1021，大端 | XMODEM 协议 |
| CRC32 | 4 字节 | 标准 CRC32，小端 | ZIP, PNG, Ethernet |

## 日志级别

- **INFO** - 普通信息（黑色）
- **SUCCESS** - 成功信息（绿色）
- **WARNING** - 警告信息（橙色）
- **ERROR** - 错误信息（红色）

## 集成到串口工具

本工具已成功集成到串口工具项目中。详细集成方法请参考 [SERIAL_TOOL_INTEGRATION.md](SERIAL_TOOL_INTEGRATION.md)。

## 文档说明

- **[README.md](README.md)** - 本文档，快速入门和 API 参考
- **[CHANGELOG.md](CHANGELOG.md)** - 版本更新日志和功能变更记录
- **[SERIAL_TOOL_INTEGRATION.md](SERIAL_TOOL_INTEGRATION.md)** - 串口工具集成指南（详细配置参数）
- **[INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md)** - 集成完成清单和测试结果

## 故障排查

### 问题 1: 串口打开失败
- 检查串口是否被其他程序占用
- 确认串口号正确
- 检查串口驱动是否安装

### 问题 2: ACK 超时
- 增加超时时间
- 检查设备是否正常响应
- 使用串口调试工具确认设备行为

### 问题 3: ACK 验证失败
- 查看日志中的实际接收数据
- 调整 ACK 预期数据和格式
- 尝试使用 OR 模式

### 问题 4: 下载速度慢
- 增大数据包大小
- 检查波特率设置
- 禁用不必要的 ACK 验证

## 开发计划

- [ ] 断点续传支持
- [ ] 自动重试机制
- [ ] 固件校验（整体 CRC）
- [ ] 多文件下载
- [ ] 下载记录保存
- [ ] 配置预设功能

---

## 版本历史

详细更新日志请参考 [CHANGELOG.md](CHANGELOG.md)。

**当前版本**: 2.0 (2026-01-14)
- ✅ 分离的 ACK 配置
- ✅ 实时输入验证
- ✅ 转义字符支持
- ✅ 日志过滤功能
- ✅ 代码优化（减少 ~40% 重复）

---

**作者**: GuoHowe
**项目**: firmware_downloader_project
**许可**: MIT
