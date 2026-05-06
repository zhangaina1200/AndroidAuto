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
    parser.add_argument('--locate', metavar='TEMPLATE', help='在截图上定位模板图像元素')
    parser.add_argument('--compare', nargs=2, metavar=('IMG1', 'IMG2'), help='对比两张图片')
    parser.add_argument('--threshold', type=float, default=0.8, help='匹配阈值 (默认: 0.8)')
    parser.add_argument('--output', '-o', metavar='FILE', help='输出文件路径')

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

    # 处理图像识别 - 定位元素
    if args.locate:
        from image_identify import locate_element_on_image, highlight_elements_on_image
        d = device.connect_device()
        screenshot_path = device.take_screenshot(d, '/tmp/_screen.png')
        matches = locate_element_on_image(screenshot_path, args.locate, args.threshold)
        print(f"找到 {len(matches)} 个匹配位置:")
        for i, (x, y, w, h, conf) in enumerate(matches):
            print(f"  #{i+1}: 位置({x}, {y}) 大小({w}x{h}) 置信度={conf:.2f}")
        output = args.output or 'locate_result.png'
        highlight_elements_on_image(screenshot_path, matches, output)
        print(f"结果已保存到: {output}")
        return

    # 处理图像对比
    if args.compare:
        from image_identify import compare_images
        img1, img2 = args.compare
        result = compare_images(img1, img2, threshold=30, output_path=args.output)
        print(f"相似度: {result['similarity']*100:.1f}%")
        print(f"发现 {len(result['diff_regions'])} 个差异区域:")
        for i, (x, y, w, h) in enumerate(result['diff_regions']):
            print(f"  #{i+1}: 位置({x}, {y}) 大小({w}x{h})")
        if args.output:
            print(f"差异图像已保存到: {args.output}")
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
