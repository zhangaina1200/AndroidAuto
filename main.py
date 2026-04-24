"""
AndroidAuto - Android设备自动化测试工具
支持 Android (uiautomator2) 和 HarmonyOS (HDC) 设备
"""
import uiautomator2 as u2
from PIL import Image
import os
import glob
import re
import subprocess
import argparse
import operations as ops
import operations_harmony as ops_harmony


def connect_device():
    """连接USB设备，自动检测设备类型"""
    device_type = ops_harmony.detect_device_type()
    if device_type == 'harmony':
        return ops_harmony.connect()
    else:
        return ops.connect()


def get_device_info(device):
    """获取设备信息"""
    device_type = ops_harmony.detect_device_type()
    if device_type == 'harmony':
        # HarmonyOS 设备信息
        w, h = device.get_screen_size()
        return {
            'productName': 'HarmonyOS Device',
            'sdkInt': 'Unknown',
            'displayWidth': w,
            'displayHeight': h,
            'currentPackage': ops_harmony.get_current_app(device) or 'Unknown',
        }
    else:
        # Android 设备信息
        info = device.device.info
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
    device_type = ops_harmony.detect_device_type()
    device = connect_device()

    if device_type == 'harmony':
        # HarmonyOS 使用 operations_harmony
        ops_harmony.screenshot(device, filename)
        print(f"截图已保存: {os.path.abspath(filename)}")
    else:
        # Android 使用 uiautomator2
        image = device.device.screenshot()
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


def parse_version_from_filename(filename):
    """
    从APK文件名解析版本号
    例如: suunto-playstore-release-6_9_3-308.apk -> (6, 9, 3, 308)
    """
    # 匹配 versionPattern 如 6_9_3-308 或 6.9.3-308
    match = re.search(r'(\d+)[_.-](\d+)[_.-](\d+)[-.](\d+)', filename)
    if match:
        return tuple(int(x) for x in match.groups())
    return None


def get_package_name_from_apk(apk_path):
    """
    从APK文件获取包名
    尝试多种方法：aapt, apkanalyzer, 或从文件名推断
    """
    # 方法1: 尝试 aapt (Android SDK build-tools)
    try:
        result = subprocess.run(
            ['aapt', 'dump', 'badging', apk_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            match = re.search(r"package: name='([^']+)'", result.stdout)
            if match:
                return match.group(1)
    except Exception:
        pass

    # 方法2: 从文件名推断常见包名模式
    basename = os.path.basename(apk_path)
    # suunto-playstore-release-6_9_3-308.apk -> com.suunto.application
    # sportstracker-playstore-release-6_9_3-308.apk -> com.sportstracker
    name_part = re.sub(r'[-_]?\d+[_-]\d+[_-]\d+[_-]\d+\.apk$', '', basename)
    name_part = name_part.replace('-playstore', '').replace('-china', '').replace('-release', '').replace('-debug', '')

    # 常见包名映射
    package_mappings = {
        'suunto': 'com.suunto.application',
        'sportstracker': 'com.sportstracker',
    }

    for key, pkg in package_mappings.items():
        if key in name_part.lower():
            return pkg

    return None


def get_installed_packages(device_serial):
    """获取设备上所有已安装的包名"""
    try:
        result = subprocess.run(
            ['adb', '-s', device_serial, 'shell', 'pm', 'list', 'packages'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            packages = []
            for line in result.stdout.strip().split('\n'):
                if 'package:' in line:
                    packages.append(line.replace('package:', '').strip())
            return packages
    except Exception:
        pass
    return []


def get_installed_version(device_serial, package_name):
    """
    获取设备上已安装应用的版本号
    返回: (version_code, version_name) 或 None
    """
    try:
        result = subprocess.run(
            ['adb', '-s', device_serial, 'shell', 'dumpsys', 'package', package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            output = result.stdout
            # 解析 versionCode
            version_code_match = re.search(r'versionCode=(\d+)', output)
            # 解析 versionName
            version_name_match = re.search(r'versionName=([\d.]+)', output)
            if version_code_match and version_name_match:
                return (int(version_code_match.group(1)), version_name_match.group(1))
    except Exception as e:
        print(f"  [WARN] 获取已安装版本失败: {e}")
    return None


def uninstall_app(device_serial, package_name):
    """卸载应用"""
    try:
        print(f"  正在卸载: {package_name} ...")
        result = subprocess.run(
            ['adb', '-s', device_serial, 'uninstall', package_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"  [OK] 卸载成功")
            return True
        else:
            print(f"  [FAIL] 卸载失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  [ERROR] 卸载出错: {e}")
        return False


def compare_versions(v1, v2):
    """
    比较两个版本号
    v1 > v2 返回 1, v1 < v2 返回 -1, v1 == v2 返回 0
    v1 和 v2 格式: (major, minor, patch, build) 元组
    """
    for i in range(min(len(v1), len(v2))):
        if v1[i] > v2[i]:
            return 1
        elif v1[i] < v2[i]:
            return -1
    if len(v1) > len(v2):
        return 1
    elif len(v1) < len(v2):
        return -1
    return 0


def install_apk_files(apk_folder_path, force_install=False):
    """
    安装指定文件夹中的所有APK文件
    使用 adb install 命令安装APK
    :param apk_folder_path: 包含APK文件的文件夹路径
    :param force_install: 是否强制安装（忽略版本比较）
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
            print(f"\n正在安装: {apk_name} ...")

            # 从APK获取真实包名
            apk_package = get_package_name_from_apk(apk_file)
            if apk_package:
                print(f"  APK包名: {apk_package}")

            # 解析APK版本
            apk_version = parse_version_from_filename(apk_name)
            if not apk_version:
                print(f"  [WARN] 无法解析APK版本，将直接安装")
            else:
                apk_version_str = f"{apk_version[0]}.{apk_version[1]}.{apk_version[2]}-{apk_version[3]}"
                print(f"  APK版本: {apk_version_str}")

                # 如果获取到包名，检查已安装版本
                if apk_package:
                    installed = get_installed_version(device_serial, apk_package)
                    if installed:
                        print(f"  已安装版本: {installed[1]} (code: {installed[0]})")
                        installed_version_tuple = parse_version_from_filename(f"xxx-{installed[1]}-{installed[0]}")
                        if installed_version_tuple:
                            cmp = compare_versions(installed_version_tuple, apk_version)
                            if cmp > 0:
                                print(f"  [SKIP] 已安装版本 ({installed[1]}) 高于目标版本 ({apk_version_str})")
                                if not force_install:
                                    print(f"         使用 --force 参数可强制安装")
                                    continue
                            elif cmp == 0:
                                print(f"  [SKIP] 版本相同，无需安装")
                                continue
                            else:
                                print(f"  目标版本低于已安装版本，将先卸载再安装")
                                uninstall_app(device_serial, apk_package)

            # 执行安装
            result = subprocess.run(
                ['adb', '-s', device_serial, 'install', '-r', apk_file],
                capture_output=True,
                text=True,
                timeout=120
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
    parser.add_argument('--install', nargs='?', const='latest', metavar='VERSION',
                        help='安装APK (可选: 指定版本如 6.9.3-308，默认安装最新版本)')
    parser.add_argument('--force', action='store_true', help='强制安装（允许降级）')
    parser.add_argument('--all', action='store_true', help='运行所有功能')
    parser.add_argument('--run', metavar='FILE', help='运行 YAML 配置文件')
    parser.add_argument('--schedule', action='store_true', help='启动定时任务调度器')
    parser.add_argument('--config', metavar='FILE', help='定时任务配置文件 (默认: config/schedule_config.yaml)')

    args = parser.parse_args()

    # 如果没有任何参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n示例:")
        print("  python main.py --info              # 获取设备信息")
        print("  python main.py --screenshot        # 截取屏幕")
        print("  python main.py --install           # 安装最新版本APK")
        print("  python main.py --install 6.9.3-308 # 安装指定版本APK")
        print("  python main.py --install 6.9.3-308 --force # 强制安装（允许降级）")
        print("  python main.py --all              # 运行所有功能")
        print("  python main.py --run test.yaml     # 运行 YAML 配置")
        print("  python main.py --schedule         # 启动定时任务")
        return

    # 处理 YAML 运行
    if args.run:
        from runner import Runner
        runner = Runner(args.run)
        runner.run()
        return

    # 处理定时任务调度
    if args.schedule:
        from scheduler import start_scheduler
        config_path = args.config or 'config/schedule_config.yaml'
        start_scheduler(config_path)
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
        if args.install == 'latest' or args.install is True:
            # 安装最新版本
            install_latest()
        else:
            # 安装指定版本
            version = args.install
            print(f"\n开始安装指定版本 APK: {version}")
            print("-" * 40)
            # 将版本格式从 6.9.3-308 转换为 6.9.3-308（文件夹名就是版本号）
            apk_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "APK file", version)
            if os.path.exists(apk_folder):
                success_count = install_apk_files(apk_folder, force_install=args.force)
                print("-" * 40)
                print(f"APK安装完成: {success_count} 成功")
            else:
                print(f"未找到版本 {version} 的APK文件夹")
                print(f"请检查 APK file/{version} 目录是否存在")
        print()

    if args.all:
        print("操作完成!")


if __name__ == "__main__":
    import sys
    main()
