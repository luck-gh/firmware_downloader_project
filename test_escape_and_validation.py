#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试转义字符和格式验证
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firmware_downloader_project.core.protocol import ProtocolHandler


def test_escape_sequences():
    """测试转义字符解析"""
    print("=" * 60)
    print("测试转义字符解析")
    print("=" * 60)

    test_cases = [
        ("Hello\\r\\n", "Hello\r\n"),
        ("Tab\\there", "Tab\there"),
        ("Null\\x00End", "Null\x00End"),
        ("Hex\\x41BC", "HexABC"),  # \x41 = 'A'
        ("Path\\\\File", "Path\\File"),  # \\\\ = \
    ]

    for input_str, expected in test_cases:
        result = ProtocolHandler.parse_escape_sequences(input_str)
        success = result == expected
        print(f"\n  输入: {repr(input_str)}")
        print(f"  期望: {repr(expected)}")
        print(f"  结果: {repr(result)}")
        print(f"  状态: {'[OK]' if success else '[FAIL]'}")


def test_data_parsing():
    """测试数据解析"""
    print("\n" + "=" * 60)
    print("测试数据解析（支持转义字符）")
    print("=" * 60)

    # HEX 格式
    print("\n测试 HEX 格式:")
    test_cases = [
        ("0x06", b'\x06'),
        ("06 AA BB", b'\x06\xAA\xBB'),
        ("0x06 0xAA 0xBB", b'\x06\xAA\xBB'),
    ]
    for input_str, expected in test_cases:
        result = ProtocolHandler.parse_data_by_format(input_str, "HEX")
        success = result == expected
        print(f"  输入: '{input_str}' → {result.hex().upper()} {'[OK]' if success else '[FAIL]'}")

    # ASCII 格式（支持转义字符）
    print("\n测试 ASCII 格式（支持转义字符）:")
    test_cases = [
        ("Hello", b'Hello'),
        ("OK\\r\\n", b'OK\r\n'),
        ("\\x06\\x41", b'\x06A'),  # \x41 = 'A'
    ]
    for input_str, expected in test_cases:
        result = ProtocolHandler.parse_data_by_format(input_str, "ASCII")
        success = result == expected
        print(f"  输入: {repr(input_str)} → {repr(result)} {'[OK]' if success else '[FAIL]'}")

    # DEC 格式
    print("\n测试 DEC 格式:")
    test_cases = [
        ("6", b'\x06'),
        ("6 170 187", b'\x06\xAA\xBB'),
        ("65 66 67", b'ABC'),  # 65=A, 66=B, 67=C
    ]
    for input_str, expected in test_cases:
        result = ProtocolHandler.parse_data_by_format(input_str, "DEC")
        success = result == expected
        print(f"  输入: '{input_str}' → {result.hex().upper()} {'[OK]' if success else '[FAIL]'}")


def test_input_validation():
    """测试输入格式验证"""
    print("\n" + "=" * 60)
    print("测试输入格式验证")
    print("=" * 60)

    # HEX 格式验证
    print("\n测试 HEX 格式验证:")
    test_cases = [
        ("0x06", True),
        ("06 AA BB", True),
        ("ABCDEF", True),
        ("GHIJKL", False),  # 包含非十六进制字符
        ("Hello", False),
    ]
    for input_str, should_pass in test_cases:
        is_valid, msg = ProtocolHandler.validate_input_format(input_str, "HEX")
        success = is_valid == should_pass
        status = "[OK]" if success else "[FAIL]"
        print(f"  输入: '{input_str}' → {is_valid} {status}")
        if not is_valid:
            print(f"    错误信息: {msg}")

    # ASCII 格式验证（总是通过）
    print("\n测试 ASCII 格式验证:")
    test_cases = [
        "Hello",
        "OK\\r\\n",
        "任何字符都可以",
        "123!@#$%",
    ]
    for input_str in test_cases:
        is_valid, msg = ProtocolHandler.validate_input_format(input_str, "ASCII")
        print(f"  输入: {repr(input_str)} → {is_valid} [OK]")

    # DEC 格式验证
    print("\n测试 DEC 格式验证:")
    test_cases = [
        ("6", True),
        ("6 170 187", True),
        ("0 255", True),
        ("256", False),  # 超出范围
        ("-1", False),  # 负数
        ("abc", False),  # 非数字
    ]
    for input_str, should_pass in test_cases:
        is_valid, msg = ProtocolHandler.validate_input_format(input_str, "DEC")
        success = is_valid == should_pass
        status = "[OK]" if success else "[FAIL]"
        print(f"  输入: '{input_str}' → {is_valid} {status}")
        if not is_valid:
            print(f"    错误信息: {msg}")


def test_start_command():
    """测试开始命令（支持转义字符）"""
    print("\n" + "=" * 60)
    print("测试开始命令构建（支持转义字符）")
    print("=" * 60)

    test_cases = [
        "START_DOWNLOAD",
        "FLASH\\r\\n",
        "\\x01\\x02\\x03",
    ]

    for cmd in test_cases:
        result = ProtocolHandler.build_start_command(cmd)
        print(f"\n  命令: {repr(cmd)}")
        print(f"  字节: {repr(result)}")
        print(f"  HEX:  {result.hex().upper()}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("固件下载工具 - 转义字符和格式验证测试")
    print("=" * 60)

    try:
        test_escape_sequences()
        test_data_parsing()
        test_input_validation()
        test_start_command()

        print("\n" + "=" * 60)
        print("[OK] 所有测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
