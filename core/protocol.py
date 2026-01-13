#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
协议处理模块
包含 ACK 验证器和 CRC 计算
"""

import struct


class AckValidator:
    """ACK 验证器 - 支持多种验证方式"""

    def __init__(self, config):
        """
        初始化验证器

        Args:
            config: ACK 配置字典
                - check_length: bool, 是否检查长度
                - expected_length: int, 预期长度
                - check_data: bool, 是否检查数据
                - expected_data: str, 预期数据
                - data_format: str, 数据格式 ("HEX"/"ASCII"/"DEC")
                - check_crc: bool, 是否检查 CRC
                - crc_type: str, CRC 类型
                - check_mode: str, 检查模式 ("AND"/"OR")
        """
        self.config = config

    def validate(self, received_data: bytes) -> tuple:
        """
        验证接收到的 ACK 数据

        Args:
            received_data: 接收到的字节数据

        Returns:
            (is_valid, message): 验证结果和详细消息
        """
        results = []

        # 1. 长度判断
        if self.config.get('check_length', False):
            length_valid = self._check_length(received_data)
            results.append(('length', length_valid))

        # 2. 数据匹配判断
        if self.config.get('check_data', False):
            data_valid = self._check_data(received_data)
            results.append(('data', data_valid))

        # 3. CRC 校验判断
        if self.config.get('check_crc', False):
            crc_valid = self._check_crc(received_data)
            results.append(('crc', crc_valid))

        # 如果没有任何验证项，默认通过
        if not results:
            return True, "无验证项，默认通过"

        # 根据逻辑模式判断
        check_mode = self.config.get('check_mode', 'AND')

        if check_mode == 'AND':
            # 全部满足
            is_valid = all(result[1] for result in results)
        else:  # OR
            # 任一满足
            is_valid = any(result[1] for result in results)

        # 生成详细消息
        message = self._generate_message(results, is_valid, received_data)

        return is_valid, message

    def _check_length(self, data: bytes) -> bool:
        """检查长度"""
        expected = self.config.get('expected_length', 1)
        actual = len(data)
        return actual == expected

    def _check_data(self, data: bytes) -> bool:
        """检查数据匹配"""
        expected_str = self.config.get('expected_data', '')
        data_format = self.config.get('data_format', 'HEX')

        try:
            expected_bytes = ProtocolHandler.parse_data_by_format(expected_str, data_format)
            return data == expected_bytes
        except Exception:
            return False

    def _check_crc(self, data: bytes) -> bool:
        """检查 CRC"""
        crc_type = self.config.get('crc_type', 'CRC16-MODBUS')

        # 确定 CRC 长度
        if crc_type.startswith('CRC16'):
            crc_len = 2
        elif crc_type.startswith('CRC32'):
            crc_len = 4
        else:
            crc_len = 1

        if len(data) < crc_len:
            return False

        # 分离数据和 CRC
        payload = data[:-crc_len]
        received_crc = data[-crc_len:]

        # 计算 CRC
        calculated_crc = CrcCalculator.calculate(payload, crc_type)

        return calculated_crc == received_crc

    def _parse_hex_string(self, hex_str: str) -> bytes:
        """解析十六进制字符串"""
        # 移除 0x 前缀和空格
        hex_str = hex_str.replace('0x', '').replace('0X', '').replace(' ', '')
        return bytes.fromhex(hex_str)

    def _generate_message(self, results: list, is_valid: bool, data: bytes) -> str:
        """生成验证消息"""
        if not results:
            return "无验证项"

        details = []
        for check_type, result in results:
            status = "[OK]" if result else "[FAIL]"
            if check_type == 'length':
                expected_len = self.config.get('expected_length', 1)
                actual_len = len(data)
                details.append(f"{status} 长度 (期望:{expected_len}, 实际:{actual_len})")
            elif check_type == 'data':
                data_hex = data.hex().upper()
                details.append(f"{status} 数据匹配 (收到:{data_hex})")
            elif check_type == 'crc':
                details.append(f"{status} CRC 校验")

        result_str = "通过" if is_valid else "失败"
        mode_str = self.config.get('check_mode', 'AND')

        return f"ACK 验证 {result_str} [{mode_str}]: {', '.join(details)}"


class CrcCalculator:
    """CRC 计算器 - 支持多种 CRC 算法"""

    @staticmethod
    def calculate(data: bytes, crc_type: str) -> bytes:
        """
        计算 CRC

        Args:
            data: 输入数据
            crc_type: CRC 类型

        Returns:
            CRC 字节串
        """
        if crc_type == 'CRC16-MODBUS':
            return CrcCalculator._crc16_modbus(data)
        elif crc_type == 'CRC16-CCITT':
            return CrcCalculator._crc16_ccitt(data)
        elif crc_type == 'CRC16-XMODEM':
            return CrcCalculator._crc16_xmodem(data)
        elif crc_type == 'CRC32':
            return CrcCalculator._crc32(data)
        else:
            return b'\x00\x00'

    @staticmethod
    def _crc16_modbus(data: bytes) -> bytes:
        """CRC16-MODBUS 算法 (常用于 Modbus 协议)"""
        crc = 0xFFFF

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1

        # 小端序
        return struct.pack('<H', crc)

    @staticmethod
    def _crc16_ccitt(data: bytes) -> bytes:
        """CRC16-CCITT 算法 (初始值 0xFFFF)"""
        crc = 0xFFFF

        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF

        # 大端序
        return struct.pack('>H', crc)

    @staticmethod
    def _crc16_xmodem(data: bytes) -> bytes:
        """CRC16-XMODEM 算法 (初始值 0x0000)"""
        crc = 0x0000

        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF

        # 大端序
        return struct.pack('>H', crc)

    @staticmethod
    def _crc32(data: bytes) -> bytes:
        """CRC32 算法 (标准 CRC32)"""
        import binascii
        crc = binascii.crc32(data) & 0xFFFFFFFF

        # 小端序
        return struct.pack('<I', crc)


class ProtocolHandler:
    """协议处理器 - 处理命令和数据包"""

    @staticmethod
    def parse_escape_sequences(text: str) -> str:
        """
        解析转义字符
        支持: \\r \\n \\t \\0 \\x## (十六进制)

        Args:
            text: 包含转义字符的文本

        Returns:
            解析后的文本
        """
        # 使用 decode('unicode_escape') 会有问题，手动处理
        result = text.replace('\\r', '\r')
        result = result.replace('\\n', '\n')
        result = result.replace('\\t', '\t')
        result = result.replace('\\0', '\0')
        result = result.replace('\\\\', '\\')  # 转义的反斜杠

        # 处理 \xHH 格式
        import re
        hex_pattern = r'\\x([0-9a-fA-F]{2})'
        result = re.sub(hex_pattern, lambda m: chr(int(m.group(1), 16)), result)

        return result

    @staticmethod
    def build_start_command(command: str) -> bytes:
        """
        构建开始命令（支持转义字符）

        Args:
            command: ASCII 命令字符串（可包含转义字符如 \\r\\n）

        Returns:
            命令字节串
        """
        # 解析转义字符
        parsed_command = ProtocolHandler.parse_escape_sequences(command)
        return parsed_command.encode('latin-1')  # 使用 latin-1 以支持所有字节值

    @staticmethod
    def build_data_packet(data: bytes, add_crc: bool = False, crc_type: str = 'CRC16-MODBUS') -> bytes:
        """
        构建数据包

        Args:
            data: 原始数据
            add_crc: 是否添加 CRC
            crc_type: CRC 类型

        Returns:
            数据包（可能包含 CRC）
        """
        if add_crc:
            crc = CrcCalculator.calculate(data, crc_type)
            return data + crc
        else:
            return data

    @staticmethod
    def parse_hex_input(hex_str: str) -> bytes:
        """
        解析用户输入的十六进制字符串
        支持格式: "0x06", "06", "06 AA BB", "0x06 0xAA 0xBB"

        Args:
            hex_str: 十六进制字符串

        Returns:
            字节串
        """
        # 移除空格，分割
        parts = hex_str.replace(' ', '').replace('0x', '').replace('0X', '')

        # 确保是偶数长度
        if len(parts) % 2 != 0:
            parts = '0' + parts

        return bytes.fromhex(parts)

    @staticmethod
    def parse_data_by_format(data_str: str, data_format: str) -> bytes:
        """
        根据格式解析数据字符串（支持转义字符）

        Args:
            data_str: 数据字符串
            data_format: 格式 ("HEX"/"ASCII"/"DEC")

        Returns:
            字节串

        Raises:
            ValueError: 格式错误
        """
        try:
            if data_format == 'HEX':
                return ProtocolHandler.parse_hex_input(data_str)
            elif data_format == 'ASCII':
                # 解析转义字符
                parsed_str = ProtocolHandler.parse_escape_sequences(data_str)
                return parsed_str.encode('latin-1')
            elif data_format == 'DEC':
                # 十进制数字列表 (如 "6 170 187")
                numbers = [int(x.strip()) for x in data_str.split() if x.strip()]
                return bytes(numbers)
            else:
                raise ValueError(f"不支持的格式: {data_format}")
        except Exception as e:
            raise ValueError(f"解析失败: {str(e)}")

    @staticmethod
    def validate_input_format(data_str: str, data_format: str) -> tuple:
        """
        验证输入格式是否正确

        Args:
            data_str: 数据字符串
            data_format: 格式 ("HEX"/"ASCII"/"DEC")

        Returns:
            (is_valid, error_message)
        """
        if not data_str:
            return False, "输入不能为空"

        try:
            if data_format == 'HEX':
                # 验证十六进制格式
                test_str = data_str.replace(' ', '').replace('0x', '').replace('0X', '')
                if not all(c in '0123456789ABCDEFabcdef' for c in test_str):
                    return False, "只能包含十六进制字符 (0-9, A-F)"
                return True, ""

            elif data_format == 'ASCII':
                # ASCII 格式允许任何字符和转义序列
                return True, ""

            elif data_format == 'DEC':
                # 验证十进制格式
                parts = data_str.split()
                for part in parts:
                    num = int(part)
                    if not (0 <= num <= 255):
                        return False, f"数字 {num} 超出范围 (0-255)"
                return True, ""

            else:
                return False, f"未知格式: {data_format}"

        except ValueError as e:
            return False, str(e)

