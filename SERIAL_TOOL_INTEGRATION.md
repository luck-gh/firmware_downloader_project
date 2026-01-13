# 固件下载工具集成到串口工具 (v2.0)

## 集成完成说明

已成功将 `firmware_downloader_project` v2.0 集成到 `serial_tool_project` 中。

**v2.0 主要更新**:
- ✅ 分离开始命令ACK和数据包ACK配置
- ✅ 输入格式实时验证(HEX/ASCII/DEC)
- ✅ 转义字符支持(\r\n\t\0\xHH)
- ✅ 代码复用优化(~40%减少)

---

## 集成内容

### 1. 配置管理器 (config_manager.py)

**新增默认配置** (v2.0 格式):
```python
"firmware_downloader": {
    "path": "",
    "enabled": False,
    "packet_size": 256,
    "start_command": "START_DOWNLOAD",
    "add_packet_crc": False,
    "packet_crc_type": "CRC16-MODBUS",

    # 开始命令 ACK 配置 (不包含CRC)
    "wait_start_ack": False,
    "start_ack_timeout": 1000,
    "start_ack_check_length": True,
    "start_ack_expected_length": 1,
    "start_ack_check_data": False,
    "start_ack_expected_data": "0x06",
    "start_ack_data_format": "HEX",
    "start_ack_check_mode": "AND",

    # 数据包 ACK 配置 (包含CRC)
    "wait_packet_ack": False,
    "packet_ack_timeout": 1000,
    "packet_ack_check_length": True,
    "packet_ack_expected_length": 1,
    "packet_ack_check_data": False,
    "packet_ack_expected_data": "0x06",
    "packet_ack_data_format": "HEX",
    "packet_ack_check_crc": False,
    "packet_ack_crc_type": "CRC16-MODBUS",
    "packet_ack_check_mode": "AND"
}
```

**新增方法**:
- `get_firmware_downloader_params()` - 获取固件下载器参数(v2.0格式)

### 2. 主窗口 (main_window.py)

**新增按钮**:
- 在"工具相关"组中添加 "固件下载" 按钮（位于 Bin转Hex 下方）
- 连接点击事件到 `self.open_firmware_downloader()`

### 3. 基础控件 (base_widgets.py)

**新增方法**:
```python
def open_firmware_downloader(self):
    """打开固件下载工具"""
```

**功能**:
1. 支持自定义路径启动（通过配置的 path）
2. 支持内置模块导入（自动查找 firmware_downloader_project）
3. 自动传递串口配置参数（端口、波特率等）
4. 自动加载用户配置的默认参数
5. 错误提示和调试信息输出

### 4. 配置对话框 (config_dialog.py)

**已自动集成**:
- 由于使用了通用的 4 列布局和工具注册表机制
- 固件下载工具会自动出现在配置对话框中
- 点击"参数"按钮可以配置所有下载参数

**新增方法**:
```python
def _open_firmware_downloader_params_dialog(self):
    """打开固件下载器参数配置对话框"""
```

---

## 使用方法

### 启用下载工具

1. 点击主窗口左侧的**"配置"**按钮
2. 在"工具路径"区域找到**"固件下载工具"**
3. 勾选启用复选框
4. (可选) 设置自定义路径，或留空使用内置集成
5. 点击"参数"按钮配置下载参数:
   - **包大小**: 128/256/512/1024 字节
   - **开始命令**: ASCII 命令字符串
   - **超时时间**: ACK 超时（毫秒）
   - **数据包 CRC**: 是否在数据包后追加 CRC
   - **ACK 配置**:
     - 是否等待 ACK
     - 长度判断、数据匹配、CRC 校验
     - 判断逻辑（AND/OR）
6. 点击"OK"保存

### 使用下载工具

1. 确保串口已连接（主窗口中已配置串口）
2. 点击左侧"工具相关"组中的**"固件下载"**按钮
3. 下载工具窗口会自动应用:
   - 当前串口配置（端口、波特率等）
   - 配置的默认下载参数
4. 选择或拖放 .bin 文件
5. (可选) 调整参数
6. 点击"开始下载"

---

## 配置文件格式 (config.json)

### v2.0 配置格式

```json
{
    "tools": {
        "firmware_downloader": {
            "path": "",
            "enabled": false,
            "packet_size": 256,
            "start_command": "START_DOWNLOAD",
            "add_packet_crc": false,
            "packet_crc_type": "CRC16-MODBUS",

            "wait_start_ack": false,
            "start_ack_timeout": 1000,
            "start_ack_check_length": true,
            "start_ack_expected_length": 1,
            "start_ack_check_data": false,
            "start_ack_expected_data": "0x06",
            "start_ack_data_format": "HEX",
            "start_ack_check_mode": "AND",

            "wait_packet_ack": false,
            "packet_ack_timeout": 1000,
            "packet_ack_check_length": true,
            "packet_ack_expected_length": 1,
            "packet_ack_check_data": false,
            "packet_ack_expected_data": "0x06",
            "packet_ack_data_format": "HEX",
            "packet_ack_check_crc": false,
            "packet_ack_crc_type": "CRC16-MODBUS",
            "packet_ack_check_mode": "AND"
        }
    }
}
```

### 参数说明 (v2.0)

#### 基本配置

| 参数 | 类型 | 可选值 | 说明 |
|------|------|--------|------|
| `path` | string | 文件路径 | 自定义工具路径（空则使用内置） |
| `enabled` | boolean | true/false | 是否启用 |
| `packet_size` | integer | 1-4096 | 数据包大小（字节） |
| `start_command` | string | ASCII字符串 | 开始命令（支持转义字符\r\n） |
| `add_packet_crc` | boolean | true/false | 数据包追加 CRC |
| `packet_crc_type` | string | CRC16-MODBUS/CCITT/XMODEM/CRC32 | 数据包 CRC 类型 |

#### 开始命令 ACK 配置

| 参数 | 类型 | 可选值 | 说明 |
|------|------|--------|------|
| `wait_start_ack` | boolean | true/false | 是否等待开始命令 ACK |
| `start_ack_timeout` | integer | 100-10000 | 超时时间（毫秒） |
| `start_ack_check_length` | boolean | true/false | 检查 ACK 长度 |
| `start_ack_expected_length` | integer | 1-256 | 预期 ACK 长度 |
| `start_ack_check_data` | boolean | true/false | 检查 ACK 数据 |
| `start_ack_expected_data` | string | HEX/ASCII/DEC | 预期 ACK 数据（支持转义字符） |
| `start_ack_data_format` | string | HEX/ASCII/DEC | ACK 数据格式 |
| `start_ack_check_mode` | string | AND/OR | 判断逻辑 |

#### 数据包 ACK 配置

| 参数 | 类型 | 可选值 | 说明 |
|------|------|--------|------|
| `wait_packet_ack` | boolean | true/false | 是否等待数据包 ACK |
| `packet_ack_timeout` | integer | 100-10000 | 超时时间（毫秒） |
| `packet_ack_check_length` | boolean | true/false | 检查 ACK 长度 |
| `packet_ack_expected_length` | integer | 1-256 | 预期 ACK 长度 |
| `packet_ack_check_data` | boolean | true/false | 检查 ACK 数据 |
| `packet_ack_expected_data` | string | HEX/ASCII/DEC | 预期 ACK 数据（支持转义字符） |
| `packet_ack_data_format` | string | HEX/ASCII/DEC | ACK 数据格式 |
| `packet_ack_check_crc` | boolean | true/false | 检查 ACK CRC（仅数据包ACK） |
| `packet_ack_crc_type` | string | CRC16-MODBUS/CCITT/XMODEM/CRC32 | ACK CRC 类型 |
| `packet_ack_check_mode` | string | AND/OR | 判断逻辑 |

---

## 启动方式

### 方式 1: 使用内置集成（推荐）

**配置**:
```json
{
    "path": "",
    "enabled": true,
    "packet_size": 256,
    "wait_ack": true,
    "ack_check_data": true,
    "ack_expected_data": "0x06"
}
```

**效果**:
- 自动查找 `firmware_downloader_project` 目录
- 以模块形式导入并显示
- 自动传递当前串口配置
- 应用配置的默认参数

### 方式 2: 使用外部可执行文件

**配置**:
```json
{
    "path": "D:/Tools/FirmwareDownloader.exe",
    "enabled": true,
    "packet_size": 512
}
```

**效果**:
- 启动外部 exe 文件
- 参数通过命令行传递

---

## 配置示例 (v2.0)

### 示例 1: 简单下载（无 ACK）

适用于设备不需要确认的场景。

```json
{
    "firmware_downloader": {
        "path": "",
        "enabled": true,
        "packet_size": 256,
        "start_command": "DOWNLOAD",
        "wait_start_ack": false,
        "wait_packet_ack": false
    }
}
```

### 示例 2: 开始命令需要确认 (ASCII格式)

开始命令需要 "OK\r\n" 确认，数据包不需要ACK。

```json
{
    "firmware_downloader": {
        "path": "",
        "enabled": true,
        "packet_size": 256,
        "start_command": "START_FLASH\\r\\n",
        "wait_start_ack": true,
        "start_ack_timeout": 2000,
        "start_ack_check_data": true,
        "start_ack_expected_data": "OK\\r\\n",
        "start_ack_data_format": "ASCII",
        "wait_packet_ack": false
    }
}
```

### 示例 3: 数据包需要固定 ACK (0x06)

开始命令不需要确认，每包数据都返回固定的 ACK 字节。

```json
{
    "firmware_downloader": {
        "path": "",
        "enabled": true,
        "packet_size": 256,
        "timeout": 1000,
        "start_command": "START_FLASH",
        "wait_start_ack": false,
        "wait_packet_ack": true,
        "packet_ack_timeout": 1000,
        "packet_ack_check_length": true,
        "packet_ack_expected_length": 1,
        "packet_ack_check_data": true,
        "packet_ack_expected_data": "0x06",
        "packet_ack_data_format": "HEX",
        "packet_ack_check_mode": "AND"
    }
}
```

### 示例 4: 数据包带 CRC16 + ACK 带 CRC 校验

适用于需要数据完整性保护的场景。

```json
{
    "firmware_downloader": {
        "path": "",
        "enabled": true,
        "packet_size": 512,
        "start_command": "UPDATE",
        "add_packet_crc": true,
        "packet_crc_type": "CRC16-MODBUS",
        "wait_start_ack": false,
        "wait_packet_ack": true,
        "packet_ack_timeout": 2000,
        "packet_ack_check_length": true,
        "packet_ack_expected_length": 3,
        "packet_ack_check_crc": true,
        "packet_ack_crc_type": "CRC16-MODBUS",
        "packet_ack_check_mode": "AND"
    }
}
```

### 示例 5: 开始和数据包都需要不同的 ACK

开始命令期望 "OK\r\n"，数据包期望 0x06。

```json
{
    "firmware_downloader": {
        "path": "",
        "enabled": true,
        "packet_size": 256,
        "start_command": "DOWNLOAD\\r\\n",
        "wait_start_ack": true,
        "start_ack_timeout": 2000,
        "start_ack_check_data": true,
        "start_ack_expected_data": "OK\\r\\n",
        "start_ack_data_format": "ASCII",
        "wait_packet_ack": true,
        "packet_ack_timeout": 1000,
        "packet_ack_check_data": true,
        "packet_ack_expected_data": "0x06",
        "packet_ack_data_format": "HEX"
    }
}
```

---

## 文件关系图

```
serial_tool_project/
├── main_window.py                    # 添加 firmware_downloader_btn 按钮
├── managers/
│   └── config_manager.py             # 添加固件下载器配置和参数获取
├── widgets/
│   └── base_widgets.py               # 添加 open_firmware_downloader() 方法
└── dialogs/
    └── config_dialog.py              # 添加固件下载器参数配置界面

firmware_downloader_project/
├── firmware_downloader_dialog.py     # 主对话框（可独立运行或集成）
├── core/
│   ├── downloader.py                 # 下载核心逻辑
│   └── protocol.py                   # 协议处理（ACK、CRC）
└── widgets/
    └── widgets.py                    # 自定义控件（拖放、进度、日志）
```

---

## 集成特性

✅ **无缝集成**: 在串口工具中一键打开
✅ **参数传递**: 自动传递串口配置
✅ **参数记忆**: 自动应用配置的默认参数
✅ **独立可选**: 可启用/禁用，不影响主工具
✅ **灵活路径**: 支持内置、外部 exe、Python 脚本
✅ **配置持久化**: 参数保存在 config.json 中
✅ **错误处理**: 完善的异常捕获和提示

---

## 注意事项

### 1. 路径配置
- **留空**: 使用内置集成（推荐）
- **指定路径**: 使用外部工具

### 2. 串口配置
- 工具会自动读取主工具的当前串口配置
- 也可以在工具内独立配置串口（用于独立运行）

### 3. 默认参数
- 只在对话框初始化时应用
- 用户可以在下载工具界面中修改
- 下次打开会重新应用配置的默认值

### 4. ACK 判断逻辑
- **AND 模式**: 所有启用的检查项都必须通过
- **OR 模式**: 任意一个检查项通过即可
- 建议根据设备协议选择合适的模式

### 5. 模块查找
内置集成会按以下顺序查找 `firmware_downloader_project`:
1. 打包环境: `sys._MEIPASS`
2. 开发环境: 向上查找包含该目录的父目录（最多4层）
3. 备用: 主工程的父目录

### 6. 错误提示
- 如果模块未找到，会弹出提示对话框
- 调试信息会输出到串口工具的输出窗口
- 下载日志会在工具内实时显示

---

## 测试建议

### 测试步骤
1. 打开串口工具，连接串口
2. 点击"配置"，启用 "固件下载工具"
3. 设置不同的默认参数组合
4. 点击"固件下载"按钮，验证:
   - 对话框能否正常打开
   - 串口配置是否正确传递
   - 默认参数是否正确应用
   - 下载功能是否正常
5. 修改参数后再次打开，验证配置是否生效

### 测试用例
- [x] 内置集成启动
- [x] 串口配置传递
- [x] 默认参数应用
- [x] 参数配置修改和保存
- [x] 核心功能测试（ACK验证、CRC计算）
- [ ] 实际下载测试（需要设备）
- [ ] 错误处理（模块未找到）
- [ ] 自定义路径启动

---

**集成完成时间**: 2026-01-13
**集成人**: GuoHowe
**文档版本**: 2.0
**主要更新**:
- v2.0 (2026-01-13): 分离开始ACK和数据包ACK配置，添加转义字符支持和输入验证
- v1.0 (2026-01-13): 初始集成
