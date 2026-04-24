"""
AndroidAuto - Android设备自动化测试工具

主入口 - 纯CLI入口，核心逻辑委托给各模块
"""
import sys
import argparse
import device
import apk_manager


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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AndroidAuto - Android设备自动化测试工具')
    parser.add_argument('--info', action='store_true', help='获取设备信息')
    parser.add_argument('--screenshot', nargs='?', const='screen.png', help='截取屏幕 (可选: 指定文件名)')
    parser.add_argument('--install', action='store_true', help='安装APK')
    parser.add_argument('--version', '-v', metavar='VER', help='指定版本号 (格式: x.x.x-xxx)')
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
        print("  python main.py --install          # 安装最新版本APK")
        print("  python main.py --install -v 1.0.0-1  # 安装指定版本")
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
        d = device.connect_device()
        print("设备连接成功!")
        info = device.get_device_info(d)
        print_device_info(info)
        print()

    if args.screenshot or args.all:
        filename = args.screenshot if args.screenshot else "screen.png"
        d = device.connect_device()
        device.take_screenshot(d, filename)
        print()

    if args.install or args.all:
        if args.version:
            apk_manager.install_by_version(args.version)
        elif args.all:
            apk_manager.install_latest()
        else:
            # 非 --all 模式，提示用户输入版本或直接安装最新
            print("请选择安装方式:")
            print("  1. 安装最新版本")
            print("  2. 指定版本安装")
            choice = input("请输入选项 (1/2): ").strip()

            if choice == '2':
                version = input("请输入版本号 (格式: x.x.x-xxx，直接回车取消): ").strip()
                if version:
                    apk_manager.install_by_version(version)
                else:
                    print("已取消安装")
            else:
                apk_manager.install_latest()
        print()

    if args.all:
        print("操作完成!")


if __name__ == "__main__":
    main()
