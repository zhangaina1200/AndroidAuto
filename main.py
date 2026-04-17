"""
AndroidAuto - Android设备自动化测试工具
"""
import uiautomator2 as u2
from PIL import Image
import os
import glob
import subprocess
import argparse


def connect_device():
    """连接USB设备"""
    device = u2.connect()
    return device


def get_device_info(device):
    """获取设备信息"""
    info = device.info
    return {
        'productName': info.get('productName', 'Unknown'),
        'sdkInt': info.get('sdkInt', 'Unknown'),
        'displayWidth': info.get('displayWidth', 'Unknown'),
        'displayHeight': info.get('displayHeight', 'Unknown'),
        'currentPackage': info.get('currentPackageName', 'Unknown'),
    }


def print_device_info(info):
    """打印设备信息"""
    print("=" * 40)
    print("设备信息")
    print("=" * 40)
    print(f"产品名称: {info['productName']}")
    print(f"Sdk版本: {info['sdkInt']}")
    print(f"屏幕分辨率: {info['displayWidth']} x {info['displayHeight']}")
    print(f"当前应用: {info['currentPackage']}")
    print("=" * 40)


def take_screenshot(filename="screen.png"):
    """截取屏幕并保存"""
    device = connect_device()
    image = device.screenshot()
    image.save(filename)
    print(f"截图已保存: {os.path.abspath(filename)}")
    return filename


def get_latest_apk_folder(apk_base_path):
    """
    获取APK文件目录中最新的子文件夹
    :param apk_base_path: APK文件存放的基础目录路径
    :return: 最新子文件夹的完整路径，如果没有找到则返回None
    """
    if not os.path.exists(apk_base_path):
        print(f"APK目录不存在: {apk_base_path}")
        return None

    # 获取所有子文件夹
    subfolders = [f for f in os.listdir(apk_base_path) if os.path.isdir(os.path.join(apk_base_path, f))]

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


def install_apk_files(apk_folder_path):
    """
    安装指定文件夹中的所有APK文件
    使用 adb install 命令安装APK
    :param apk_folder_path: 包含APK文件的文件夹路径
    :return: 安装成功的APK数量
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

    # 获取当前连接的设备序列号
    device = connect_device()
    device_serial = device.serial

    success_count = 0

    for apk_file in apk_files:
        apk_name = os.path.basename(apk_file)
        try:
            print(f"正在安装: {apk_name} ...")
            # 使用 adb -s <serial> install -r 覆盖安装指定设备
            result = subprocess.run(
                ['adb', '-s', device_serial, 'install', '-r', apk_file],
                capture_output=True,
                text=True
            )
            # adb install 成功时返回0
            if result.returncode == 0:
                print(f"  [OK] 安装成功: {apk_name}")
                success_count += 1
            else:
                print(f"  [FAIL] 安装失败: {apk_name}")
                print(f"        原因: {result.stderr.strip()}")
        except Exception as e:
            print(f"  [ERROR] 安装出错: {apk_name} - {str(e)}")

    return success_count


def install_latest():
    """安装最新版本的APK"""
    apk_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "APK file")
    latest_apk_folder = get_latest_apk_folder(apk_base_path)

    if latest_apk_folder:
        print("\n开始安装APK文件...")
        print("-" * 40)
        success_count = install_apk_files(latest_apk_folder)
        print("-" * 40)
        print(f"APK安装完成: {success_count}/{len(glob.glob(os.path.join(latest_apk_folder, '*.apk')))} 成功")
    else:
        print("未找到可安装的APK文件夹")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AndroidAuto - Android设备自动化测试工具')
    parser.add_argument('--info', action='store_true', help='获取设备信息')
    parser.add_argument('--screenshot', nargs='?', const='screen.png', help='截取屏幕 (可选: 指定文件名)')
    parser.add_argument('--install', action='store_true', help='安装最新版本APK')
    parser.add_argument('--all', action='store_true', help='运行所有功能')
    parser.add_argument('--run', metavar='FILE', help='运行 YAML 配置文件')

    args = parser.parse_args()

    # 如果没有任何参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n示例:")
        print("  python main.py --info          # 获取设备信息")
        print("  python main.py --screenshot    # 截取屏幕")
        print("  python main.py --install       # 安装APK")
        print("  python main.py --all           # 运行所有功能")
        print("  python main.py --run test.yaml # 运行 YAML 配置")
        return

    # 处理 YAML 运行
    if args.run:
        from runner import Runner
        runner = Runner(args.run)
        runner.run()
        return

    # 处理各功能
    if args.info or args.all:
        print("正在连接Android设备...")
        device = connect_device()
        print("设备连接成功!")
        info = get_device_info(device)
        print_device_info(info)
        print()

    if args.screenshot or args.all:
        filename = args.screenshot if args.screenshot else "screen.png"
        take_screenshot(filename)
        print()

    if args.install or args.all:
        install_latest()
        print()

    if args.all:
        print("操作完成!")


if __name__ == "__main__":
    import sys
    main()
