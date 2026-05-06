# Suunto Android 应用自动化测试

## 概述

本测试套件用于 Suunto 中国区 Android 应用 (com.stt.android.suunto.china) 的自动化测试。

## 测试范围

- 启动与设备配对
- 主页导航 (5个 Tab)
- 训练日记与统计
- 地图/探索功能
- 运动历史记录
- 用户中心设置

## 目录结构

```
suunto_cases/                  # Suunto 测试用例目录
├── 01_startup.yaml           # 启动测试
├── 02_device_pairing.yaml    # 设备配对测试
├── 03_navigation.yaml        # 导航测试
├── 04_diary.yaml             # 训练日记测试
├── 05_sport.yaml             # 运动功能测试
├── README.md                 # 本文件
│
└── reports/                  # 测试报告目录 (自动创建)
    └── YYYY-MM-DD/           # 按日期组织
        ├── 01_startup/       # 按用例名组织
        │   ├── 01_startup.png
        │   └── run_*.log
        ├── 02_device_pairing/
        │   └── ...
        └── logs/             # 日志汇总
            └── run_*.log
```

## 执行方式

### YAML 测试脚本 (推荐)

```bash
# 运行单个测试用例
python main.py --run suunto_cases/01_startup.yaml
python main.py --run suunto_cases/02_device_pairing.yaml
python main.py --run suunto_cases/03_navigation.yaml
python main.py --run suunto_cases/04_diary.yaml
python main.py --run suunto_cases/05_sport.yaml

# 运行所有 Suunto 测试
for f in suunto_cases/0*.yaml; do python main.py --run "$f"; done
```

### pytest 测试代码

```bash
# 仅运行 Suunto 测试
pytest tests/suunto/ -v
```

## 测试用例列表

| ID | 用例名称 | 模块 | YAML 文件 |
|----|---------|------|----------|
| TC01 | 应用冷启动 | 启动与配对 | 01_startup.yaml |
| TC02 | 无设备弹窗处理 | 启动与配对 | 01_startup.yaml |
| TC03 | 设备配对按钮验证 | 启动与配对 | 02_device_pairing.yaml |
| TC04 | 底部导航栏验证 | 导航 | 02_device_pairing.yaml |
| TC05 | 切换到首页仪表盘 | 导航 | 03_navigation.yaml |
| TC06 | 切换到日历视图 | 导航 | 03_navigation.yaml |
| TC07 | 切换到探索/地图 | 导航 | 03_navigation.yaml |
| TC08 | 切换到个人中心 | 导航 | 03_navigation.yaml |
| TC09 | 查看训练统计 | 训练日记 | 04_diary.yaml |
| TC10 | 无训练数据提示 | 训练日记 | 04_diary.yaml |
| TC11 | 切换周期视图 | 训练日记 | 04_diary.yaml |
| TC12 | 首页仪表盘验证 | 运动功能 | 05_sport.yaml |
| TC16 | 地图加载验证 | 运动功能 | 05_sport.yaml |
| TC18 | 历史记录查看 | 历史记录 | 05_sport.yaml |
| TC20 | 用户中心验证 | 用户中心 | 05_sport.yaml |

## 底部导航栏坐标

屏幕分辨率 1080x2400，底部导航栏位于 y=2327 附近。

| Tab | 坐标 (x, y) | 功能 |
|-----|-------------|------|
| 首页 | (108, 2327) | 仪表盘 |
| 日历 | (324, 2327) | 日历视图 |
| 训练日记 | (540, 2327) | 训练记录 |
| 探索 | (756, 2327) | 地图探索 |
| 我的 | (972, 2327) | 个人中心 |

## 关键元素定位

### 设备配对页面元素

| Resource ID | 说明 |
|-----------|-----|
| `device_found_header` | "已找到设备" 标题 |
| `device_name` | 设备名称 |
| `device_serial` | 序列号 |
| `device_connect` | "配对" 按钮 |
| `no_signal_to_device_guidance` | 操作提示 |

## 注意事项

1. 测试前确保设备已连接 (`python main.py --info`)
2. 首次运行会弹出"无设备配对"提示，测试会自动处理
3. 截图自动保存到 `reports/YYYY-MM-DD/` 目录
4. 弹窗关闭坐标: (894, 1713)

## 依赖

- uiautomator2 >= 2.16.0
- opencv-python >= 4.5.0
- pillow >= 8.0.0
- pytest >= 6.0.0
- pyyaml >= 5.0.0