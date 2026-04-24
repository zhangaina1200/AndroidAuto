"""
AndroidAuto APK Manager Module

APK管理模块 - 提供APK下载、版本管理、安装等功能
"""
import os
import re
import glob
import subprocess

# 默认APK存放基础目录
DEFAULT_APK_BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "APK file")

# 版本号格式正则：x.x.x-xxx
VERSION_PATTERN = re.compile(r'^\d+\.\d+\.\d+-\d+$')


def is_valid_version_format(version):
    """检查版本号格式是否正确 (x.x.x-xxx)"""
    return bool(VERSION_PATTERN.match(version))


def list_available_versions(apk_base_path=None):
    """
    列出所有可用的版本

    Args:
        apk_base_path: APK基础目录

    Returns:
        list: 版本号列表
    """
    if apk_base_path is None:
        apk_base_path = DEFAULT_APK_BASE_PATH

    if not os.path.exists(apk_base_path):
        return []

    subfolders = [f for f in os.listdir(apk_base_path)
                  if os.path.isdir(os.path.join(apk_base_path, f))]
    return sorted(subfolders, reverse=True)


def get_latest_apk_folder(apk_base_path=None):
    """
    获取APK文件目录中最新的子文件夹

    Args:
        apk_base_path: APK文件存放的基础目录路径，None 则使用默认路径

    Returns:
        str: 最新子文件夹的完整路径，如果没有找到则返回None
    """
    if apk_base_path is None:
        apk_base_path = DEFAULT_APK_BASE_PATH

    if not os.path.exists(apk_base_path):
        print(f"APK目录不存在: {apk_base_path}")
        return None

    # 获取所有子文件夹
    subfolders = [f for f in os.listdir(apk_base_path)
                  if os.path.isdir(os.path.join(apk_base_path, f))]

    if not subfolders:
        print(f"在 {apk_base_path} 中未找到任何子文件夹")
        return None

    # 按修改时间排序，获取最新的文件夹
    subfolders_with_time = [
        (f, os.path.getmtime(os.path.join(apk_base_path, f))) for f in subfolders
    ]
    subfolders_with_time.sort(key=lambda x: x[1], reverse=True)
    latest_folder = subfolders_with_time[0][0]

    latest_path = os.path.join(apk_base_path, latest_folder)
    print(f"找到最新APK文件夹: {latest_folder}")
    return latest_path


def install_apk_files(apk_folder_path, device_serial=None):
    """
    安装指定文件夹中的所有APK文件
    使用 adb install 命令安装APK

    Args:
        apk_folder_path: 包含APK文件的文件夹路径
        device_serial: 设备序列号，None 则自动检测

    Returns:
        int: 安装成功的APK数量
    """
    if not apk_folder_path or not os.path.exists(apk_folder_path):
        print(f"APK文件夹无效: {apk_folder_path}")
        return 0

    # 查找所有.apk文件
    apk_pattern = os.path.join(apk_folder_path, "*.apk")
    apk_files = glob.glob(apk_pattern)

    if not apk_files:
        print(f"在 {apk_folder_path} 中未找到APK文件")
        return 0

    print(f"找到 {len(apk_files)} 个APK文件:")
    for apk in apk_files:
        print(f"  - {os.path.basename(apk)}")

    # 获取设备序列号
    if device_serial is None:
        import uiautomator2 as u2
        device = u2.connect()
        device_serial = device.serial

    success_count = 0

    for apk_file in apk_files:
        apk_name = os.path.basename(apk_file)
        try:
            print(f"正在安装: {apk_name} ...")
            result = subprocess.run(
                ['adb', '-s', device_serial, 'install', '-r', apk_file],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"  [OK] 安装成功: {apk_name}")
                success_count += 1
            else:
                print(f"  [FAIL] 安装失败: {apk_name}")
                print(f"        原因: {result.stderr.strip()}")
        except Exception as e:
            print(f"  [ERROR] 安装出错: {apk_name} - {str(e)}")

    return success_count


def install_latest(apk_base_path=None):
    """
    安装最新版本的APK

    Args:
        apk_base_path: APK文件存放的基础目录路径，None 则使用默认路径

    Returns:
        int: 安装成功的APK数量
    """
    if apk_base_path is None:
        apk_base_path = DEFAULT_APK_BASE_PATH

    latest_apk_folder = get_latest_apk_folder(apk_base_path)

    if latest_apk_folder:
        print("\n开始安装APK文件...")
        print("-" * 40)
        success_count = install_apk_files(latest_apk_folder)
        print("-" * 40)
        apk_count = len(glob.glob(os.path.join(latest_apk_folder, '*.apk')))
        print(f"APK安装完成: {success_count}/{apk_count} 成功")
        return success_count
    else:
        print("未找到可安装的APK文件夹")
        return 0


def get_apk_folder_by_version(version, apk_base_path=None):
    """
    获取指定版本的APK文件夹路径

    Args:
        version: 版本号 (格式: x.x.x-xxx)
        apk_base_path: APK基础目录

    Returns:
        str: 版本文件夹路径，不存在则返回None
    """
    if apk_base_path is None:
        apk_base_path = DEFAULT_APK_BASE_PATH

    version_folder = os.path.join(apk_base_path, version)
    if os.path.isdir(version_folder):
        return version_folder
    return None


def install_by_version(version, apk_base_path=None):
    """
    安装指定版本的APK

    Args:
        version: 版本号 (格式: x.x.x-xxx)
        apk_base_path: APK文件存放的基础目录路径，None 则使用默认路径

    Returns:
        int: 安装成功的APK数量，-1表示版本不存在或格式错误
    """
    if apk_base_path is None:
        apk_base_path = DEFAULT_APK_BASE_PATH

    # 校验版本格式
    if not is_valid_version_format(version):
        print(f"版本号格式错误: {version}")
        print("正确格式: x.x.x-xxx (例如: 1.2.3-456)")
        available = list_available_versions(apk_base_path)
        if available:
            print(f"可用版本: {', '.join(available)}")
        return -1

    version_folder = get_apk_folder_by_version(version, apk_base_path)

    if not version_folder:
        print(f"版本 {version} 不存在")
        available = list_available_versions(apk_base_path)
        if available:
            print(f"可用版本: {', '.join(available)}")
        else:
            print("未找到任何版本目录，请将APK放入 'APK file' 目录")
        return -1

    # 检查目录下是否有APK文件
    apk_pattern = os.path.join(version_folder, "*.apk")
    apk_files = glob.glob(apk_pattern)
    if not apk_files:
        print(f"版本 {version} 目录下无APK文件")
        return -1

    print(f"\n开始安装版本 {version} 的APK文件...")
    print("-" * 40)
    success_count = install_apk_files(version_folder)
    print("-" * 40)
    apk_count = len(glob.glob(os.path.join(version_folder, '*.apk')))
    print(f"APK安装完成: {success_count}/{apk_count} 成功")
    return success_count
