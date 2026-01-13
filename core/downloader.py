#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
固件下载核心模块
"""

import time
import serial
from typing import Optional, Callable
from .protocol import AckValidator, ProtocolHandler


class FirmwareDownloader:
    """固件下载器"""

    def __init__(self, port_config: dict, download_config: dict):
        """
        初始化下载器

        Args:
            port_config: 串口配置
                - port: 端口号
                - baudrate: 波特率
                - bytesize: 数据位
                - parity: 校验位
                - stopbits: 停止位
            download_config: 下载配置
                - start_command: 开始命令
                - packet_size: 包大小
                - wait_start_ack: 是否等待开始命令的 ACK
                - start_ack_timeout: 开始命令 ACK 超时时间 (ms)
                - start_ack_config: 开始命令 ACK 验证配置
                - wait_packet_ack: 是否等待数据包 ACK
                - packet_ack_timeout: 数据包 ACK 超时时间 (ms)
                - packet_ack_config: 数据包 ACK 验证配置
                - add_packet_crc: 是否添加数据包 CRC
                - packet_crc_type: 数据包 CRC 类型
        """
        self.port_config = port_config
        self.download_config = download_config
        self.serial_port: Optional[serial.Serial] = None
        self.is_running = False
        self.is_stopped = False

        # 创建开始命令 ACK 验证器
        if download_config.get('wait_start_ack', False):
            self.start_ack_validator = AckValidator(download_config.get('start_ack_config', {}))
        else:
            self.start_ack_validator = None

        # 创建数据包 ACK 验证器
        if download_config.get('wait_packet_ack', False):
            self.packet_ack_validator = AckValidator(download_config.get('packet_ack_config', {}))
        else:
            self.packet_ack_validator = None

        # 创建末尾数据包 ACK 验证器
        if download_config.get('wait_last_packet_ack', False):
            self.last_packet_ack_validator = AckValidator(download_config.get('last_packet_ack_config', {}))
        else:
            self.last_packet_ack_validator = None

    def open_port(self) -> tuple:
        """
        打开串口

        Returns:
            (success, message)
        """
        try:
            timeout_value = max(
                self.download_config.get('start_ack_timeout', 1000),
                self.download_config.get('packet_ack_timeout', 1000),
                self.download_config.get('last_packet_ack_timeout', 1000)
            ) / 1000.0  # 使用较大的超时时间，转换为秒

            self.serial_port = serial.Serial(
                port=self.port_config['port'],
                baudrate=self.port_config['baudrate'],
                bytesize=self.port_config['bytesize'],
                parity=self.port_config['parity'],
                stopbits=self.port_config['stopbits'],
                timeout=timeout_value
            )
            return True, f"成功打开串口 {self.port_config['port']} (超时={timeout_value}s)"
        except Exception as e:
            return False, f"打开串口失败: {str(e)}"

    def close_port(self):
        """关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def download(
        self,
        firmware_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None
    ) -> tuple:
        """
        下载固件

        Args:
            firmware_path: 固件文件路径
            progress_callback: 进度回调 (current, total, message)
            log_callback: 日志回调 (level, message)

        Returns:
            (success, message)
        """
        self.is_running = True
        self.is_stopped = False

        # 调试日志：记录下载开始
        if log_callback:
            port_status = "打开" if (self.serial_port and self.serial_port.is_open) else "关闭"
            log_callback("DEBUG", f"下载开始 - 串口状态: {port_status}")

        try:
            # 1. 读取固件文件
            if log_callback:
                log_callback("INFO", f"正在读取固件文件: {firmware_path}")

            with open(firmware_path, 'rb') as f:
                firmware_data = f.read()

            total_size = len(firmware_data)
            packet_size = self.download_config.get('packet_size', 256)
            total_packets = (total_size + packet_size - 1) // packet_size

            if log_callback:
                log_callback("INFO", f"固件大小: {total_size} 字节")
                log_callback("INFO", f"包大小: {packet_size} 字节")
                log_callback("INFO", f"总包数: {total_packets}")

            # 2. 发送开始命令
            start_command = self.download_config.get('start_command', '')
            if start_command:
                if log_callback:
                    log_callback("INFO", f"发送开始命令: {start_command}")

                cmd_bytes = ProtocolHandler.build_start_command(start_command)
                self.serial_port.write(cmd_bytes)

                # 等待开始命令的 ACK
                if self.download_config.get('wait_start_ack', False):
                    success, msg = self._wait_for_ack(
                        "开始命令",
                        log_callback,
                        use_start_ack=True
                    )
                    if not success:
                        return False, msg

            # 3. 循环发送数据包
            for packet_idx in range(total_packets):
                # 检查是否被停止
                if self.is_stopped:
                    if log_callback:
                        log_callback("WARNING", "下载被用户中断")
                    return False, "下载被用户中断"

                # 提取当前包数据
                start_pos = packet_idx * packet_size
                end_pos = min(start_pos + packet_size, total_size)
                packet_data = firmware_data[start_pos:end_pos]

                # 构建数据包（可能添加 CRC）
                add_crc = self.download_config.get('add_packet_crc', False)
                crc_type = self.download_config.get('packet_crc_type', 'CRC16-MODBUS')
                packet = ProtocolHandler.build_data_packet(packet_data, add_crc, crc_type)

                # 发送数据包
                self.serial_port.write(packet)

                if log_callback:
                    log_callback(
                        "INFO",
                        f"发送数据包 {packet_idx + 1}/{total_packets} "
                        f"({len(packet_data)} 字节{' + CRC' if add_crc else ''})"
                    )

                # 等待数据包 ACK（最后一包使用专门的配置）
                is_last_packet = (packet_idx == total_packets - 1)

                # 调试日志：标记最后一包
                if is_last_packet and log_callback:
                    port_status = "打开" if (self.serial_port and self.serial_port.is_open) else "关闭"
                    log_callback("DEBUG", f"最后一包数据已发送 - 串口状态: {port_status}")

                # 如果是最后一包且配置了末尾数据包 ACK，使用末尾数据包 ACK 验证器
                if is_last_packet and self.download_config.get('wait_last_packet_ack', False):
                    if log_callback:
                        log_callback("DEBUG", f"开始等待末尾数据包ACK...")
                    success, msg = self._wait_for_ack(
                        f"末尾数据包 {packet_idx + 1}",
                        log_callback,
                        use_start_ack=False,
                        use_last_packet_ack=True
                    )
                    if not success:
                        return False, msg
                # 否则，如果配置了普通数据包 ACK，使用普通数据包 ACK 验证器
                elif self.download_config.get('wait_packet_ack', False) and not is_last_packet:
                    success, msg = self._wait_for_ack(
                        f"数据包 {packet_idx + 1}",
                        log_callback,
                        use_start_ack=False,
                        use_last_packet_ack=False
                    )
                    if not success:
                        return False, msg

                # 更新进度
                if progress_callback:
                    progress = int((packet_idx + 1) / total_packets * 100)
                    progress_callback(
                        packet_idx + 1,
                        total_packets,
                        f"已发送 {packet_idx + 1}/{total_packets} 包"
                    )

            # 4. 下载完成
            if log_callback:
                port_status = "打开" if (self.serial_port and self.serial_port.is_open) else "关闭"
                log_callback("SUCCESS", f"固件下载完成！共发送 {total_packets} 包")
                log_callback("DEBUG", f"下载完成后 - 串口状态: {port_status}")

            # 5. 发送结尾字符串（如果配置）
            if self.download_config.get('send_end_string', False):
                end_string = self.download_config.get('end_string', '')
                if end_string:
                    if log_callback:
                        port_status = "打开" if (self.serial_port and self.serial_port.is_open) else "关闭"
                        log_callback("DEBUG", f"准备发送结尾字符串 - 串口状态: {port_status}")
                        log_callback("INFO", f"发送结尾字符串: {end_string}")

                    end_bytes = ProtocolHandler.build_start_command(end_string)
                    self.serial_port.write(end_bytes)

                    if log_callback:
                        port_status = "打开" if (self.serial_port and self.serial_port.is_open) else "关闭"
                        log_callback("INFO", f"结尾字符串已发送 - 串口状态: {port_status}")

            # 调试日志：记录返回前的状态
            if log_callback:
                port_status = "打开" if (self.serial_port and self.serial_port.is_open) else "关闭"
                log_callback("DEBUG", f"download() 方法即将返回 - 串口状态: {port_status}")

            return True, "下载成功"

        except FileNotFoundError:
            msg = f"文件不存在: {firmware_path}"
            if log_callback:
                log_callback("ERROR", msg)
            return False, msg

        except serial.SerialException as e:
            msg = f"串口错误: {str(e)}"
            if log_callback:
                log_callback("ERROR", msg)
            return False, msg

        except Exception as e:
            msg = f"下载失败: {str(e)}"
            if log_callback:
                log_callback("ERROR", msg)
            return False, msg

        finally:
            self.is_running = False

    def _wait_for_ack(
        self,
        context: str,
        log_callback: Optional[Callable] = None,
        use_start_ack: bool = False,
        use_last_packet_ack: bool = False
    ) -> tuple:
        """
        等待 ACK 确认

        Args:
            context: 上下文描述（用于日志）
            log_callback: 日志回调
            use_start_ack: True=使用开始命令ACK验证器, False=使用数据包ACK验证器
            use_last_packet_ack: True=使用末尾数据包ACK验证器

        Returns:
            (success, message)
        """
        # 选择对应的验证器
        if use_start_ack:
            validator = self.start_ack_validator
        elif use_last_packet_ack:
            validator = self.last_packet_ack_validator
        else:
            validator = self.packet_ack_validator

        if not validator:
            return True, "未启用 ACK 验证"

        # 选择对应的超时时间和配置
        if use_start_ack:
            timeout = self.download_config.get('start_ack_timeout', 1000) / 1000.0
            ack_config = self.download_config.get('start_ack_config', {})
        elif use_last_packet_ack:
            timeout = self.download_config.get('last_packet_ack_timeout', 1000) / 1000.0
            ack_config = self.download_config.get('last_packet_ack_config', {})
        else:
            timeout = self.download_config.get('packet_ack_timeout', 1000) / 1000.0
            ack_config = self.download_config.get('packet_ack_config', {})

        start_time = time.time()

        # 确定需要读取的字节数
        if ack_config.get('check_length', False):
            # 如果启用长度检查，使用预期长度
            expected_len = ack_config.get('expected_length', 1)
        elif ack_config.get('check_data', False):
            # 如果只启用数据匹配，计算预期数据的长度
            try:
                expected_data_str = ack_config.get('expected_data', '')
                data_format = ack_config.get('data_format', 'HEX')
                expected_bytes = ProtocolHandler.parse_data_by_format(expected_data_str, data_format)
                expected_len = len(expected_bytes)
            except:
                expected_len = 1  # 解析失败时默认读取1字节
        else:
            # 默认读取1字节
            expected_len = 1

        # 调试日志：记录开始等待
        if log_callback:
            port_status = "打开" if (self.serial_port and self.serial_port.is_open) else "关闭"
            log_callback("DEBUG", f"{context} - 开始等待ACK (预期{expected_len}字节, 超时{timeout*1000:.0f}ms, 串口状态:{port_status})")

        # 等待数据
        wait_count = 0
        while (time.time() - start_time) < timeout:
            # 检查串口状态
            if not self.serial_port or not self.serial_port.is_open:
                msg = f"{context} - 串口已关闭"
                if log_callback:
                    log_callback("ERROR", msg)
                return False, msg

            # 检查是否有足够的数据
            in_waiting = self.serial_port.in_waiting
            if in_waiting >= expected_len:
                # 调试日志：记录读取数据
                if log_callback:
                    elapsed = (time.time() - start_time) * 1000
                    log_callback("DEBUG", f"{context} - 检测到{in_waiting}字节数据 (耗时{elapsed:.0f}ms), 开始读取...")

                # 读取数据
                ack_data = self.serial_port.read(expected_len)

                # 调试日志：记录读取结果
                if log_callback:
                    ack_hex = ack_data.hex().upper() if ack_data else "无数据"
                    log_callback("DEBUG", f"{context} - 读取到数据: {ack_hex} ({len(ack_data)}字节)")

                # 验证 ACK
                is_valid, msg = validator.validate(ack_data)

                if log_callback:
                    level = "INFO" if is_valid else "ERROR"
                    log_callback(level, f"{context} - {msg}")

                if is_valid:
                    return True, "ACK 验证通过"
                else:
                    return False, f"ACK 验证失败: {msg}"

            # 每100次循环输出一次等待状态
            wait_count += 1
            if wait_count % 100 == 0 and log_callback:
                elapsed = (time.time() - start_time) * 1000
                log_callback("DEBUG", f"{context} - 等待中... (缓冲区:{in_waiting}字节, 已耗时:{elapsed:.0f}ms)")

            time.sleep(0.001)  # 减少 CPU 占用

        # 超时
        final_in_waiting = self.serial_port.in_waiting if (self.serial_port and self.serial_port.is_open) else 0
        port_status = "打开" if (self.serial_port and self.serial_port.is_open) else "关闭"
        msg = f"{context} - ACK 超时 ({timeout * 1000:.0f} ms), 串口状态:{port_status}, 缓冲区剩余:{final_in_waiting}字节"
        if log_callback:
            log_callback("ERROR", msg)
        return False, msg

    def stop(self):
        """停止下载"""
        self.is_stopped = True
