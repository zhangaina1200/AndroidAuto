# AndroidAuto

[![GitHub stars](https://img.shields.io/github/stars/zhangaina1200/AndroidAuto?style=social)](https://github.com/zhangaina1200/AndroidAuto/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/zhangaina1200/AndroidAuto?style=social)](https://github.com/zhangaina1200/AndroidAuto/network/members)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)

> Android 设备自动化测试工具 - 连接设备、获取信息、截图、安装 APK、定时任务

## Features

- **Device Connection** - Connect to Android devices via USB
- **Device Info** - Retrieve device information (model, SDK, screen resolution, current app)
- **Screenshot** - Capture device screen and save as PNG
- **APK Installation** - Batch install APK files to device
- **YAML Automation** - Write and execute automation scripts in YAML format
- **Scheduled Tasks** - Automatically launch apps at configurable time windows

## Prerequisites

- Python 3.7+
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed and in PATH

## Installation

```bash
git clone https://github.com/zhangaina1200/AndroidAuto.git
cd AndroidAuto
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Usage

### CLI Options

```bash
python main.py --help
```

| Option | Description |
|--------|-------------|
| `--info` | Retrieve and display device information |
| `--screenshot [FILE]` | Capture device screen |
| `--install` | Install latest APK |
| `--all` | Run all functions |
| `--run <FILE>` | Execute YAML configuration file |
| `--schedule` | Start scheduled task scheduler |
| `--config <FILE>` | Specify scheduler config file |

### Examples

```bash
python main.py --info                      # Get device info
python main.py --screenshot                # Take screenshot
python main.py --run my_script.yaml       # Run YAML automation
python main.py --schedule                 # Start scheduler
python main.py --schedule --config my_config.yaml  # With custom config
```

## YAML Automation

Write automation scripts in YAML format:

```bash
python main.py --run examples/example_launch_app.yaml
```

**Example YAML file:**

```yaml
app: myapp

devices:
  serial: null

steps:
  - action: launch_app
    package: com.example.app

  - action: wait_time
    seconds: 2

  - action: screenshot
    filename: result.png
```

### Supported Actions

| Action | Description |
|--------|-------------|
| `launch_app` / `stop_app` | Start or stop an app |
| `tap` / `double_tap` / `long_press` | Touch operations |
| `swipe` / `swipe_up` / `swipe_down` | Swipe gestures |
| `input_text` / `clear_text` | Text input |
| `press_key` / `press_back` / `press_home` / `press_power` | Key operations |
| `wait` / `wait_time` | Wait for element or time |
| `scroll_up` / `scroll_down` / `scroll_to_text` | Scroll operations |
| `screenshot` | Capture screen |
| `assert_exists` / `assert_text` | Assertions |

## Scheduled Tasks

Configure automatic app launching at specific time windows:

### Configuration

Edit `config/schedule_config.yaml`:

```yaml
time_windows:
  - start: "08:30"
    end: "08:45"
  - start: "18:15"
    end: "18:30"

target:
  app_package: com.example.app

device:
  serial: null

retry:
  max_attempts: 5
  interval_seconds: 10

logging:
  dir: schedules
```

### Start Scheduler

```bash
python main.py --schedule
```

The scheduler will:
1. Trigger at each window start time
2. Launch the configured app
3. Wait 30 seconds then close the app
4. Log execution results to `schedules/execution_log.db`

### Windows Scheduled Task (Optional)

To run the scheduler automatically on your PC:

1. Create the task:
```batch
schtasks /create /tn "AndroidAuto_Scheduler" /tr "E:\AndroidAuto_new\run_scheduler.bat" /sc daily /st 08:00 /ru Aina /f
```

2. The task will start daily at 08:00, which triggers the scheduler to calculate and execute at configured windows

## Project Structure

```
AndroidAuto/
├── main.py              # Main entry point (CLI)
├── operations.py         # Core operation functions
├── runner.py            # YAML configuration runner
├── scheduler.py         # Scheduled task scheduler
├── config/              # Configuration files
│   ├── schedule_config.yaml
│   └── schedule_config.example.yaml
├── examples/            # Example YAML scripts
├── screenshots/          # Screenshot output (auto-generated)
├── schedules/            # Scheduler logs and DB (auto-generated)
├── requirements.txt     # Python dependencies
└── README.md
```

## License

MIT License