"""
AndroidAuto Device Module

设备管理模块 - 提供设备连接、信息获取、截图等功能
"""
import uiautomator2 as u2
import os
import time


def connect_device(serial=None, max_retries=3, retry_interval=5):
    """
    连接USB设备，支持重试

    Args:
        serial: 设备序列号，None 则自动检测
        max_retries: 最大重试次数
        retry_interval: 重试间隔（秒）

    Returns:
        u2.Device: 设备对象
    """
    for attempt in range(1, max_retries + 1):
        try:
            device = u2.connect(serial)
            # 验证连接：尝试获取设备信息
            device.info
            return device
        except Exception as e:
            if attempt < max_retries:
                print(f"[Device] 连接失败 (尝试 {attempt}/{max_retries}): {e}")
                time.sleep(retry_interval)
            else:
                raise Exception(f"设备连接失败，已达到最大重试次数: {e}") from e


def get_device_info(device):
    """
    获取设备信息

    Args:
        device: u2.Device 对象

    Returns:
        dict: 设备信息字典
    """
    info = device.info
    return {
        'productName': info.get('productName', 'Unknown'),
        'sdkInt': info.get('sdkInt', 'Unknown'),
        'displayWidth': info.get('displayWidth', 'Unknown'),
        'displayHeight': info.get('displayHeight', 'Unknown'),
        'currentPackage': info.get('currentPackageName', 'Unknown'),
    }


def take_screenshot(device, filename="screen.png"):
    """
    截取屏幕并保存

    Args:
        device: u2.Device 对象
        filename: 保存文件名

    Returns:
        str: 截图文件绝对路径
    """
    image = device.screenshot()
    image.save(filename)
    return os.path.abspath(filename)
