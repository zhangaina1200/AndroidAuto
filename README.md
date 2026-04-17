# AndroidAuto

[![GitHub stars](https://img.shields.io/github/stars/zhangaina1200/AndroidAuto?style=social)](https://github.com/zhangaina1200/AndroidAuto/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/zhangaina1200/AndroidAuto?style=social)](https://github.com/zhangaina1200/AndroidAuto/network/members)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)

> Android 设备自动化测试工具 - 连接设备、获取信息、截图、安装 APK

## 📖 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Connect Device](#connect-device)
  - [Get Device Info](#get-device-info)
  - [Take Screenshot](#take-screenshot)
  - [Install APK](#install-apk)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- 🔌 **Device Connection** - Connect to Android devices via USB
- 📱 **Device Info** - Retrieve device information (model, SDK, screen resolution, current app)
- 📸 **Screenshot** - Capture device screen and save as PNG
- 📦 **APK Installation** - Batch install APK files to device
- 🔍 **Auto-detection** - Automatically find the latest APK folder

## 🔧 Prerequisites

- Python 3.7+
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed and in PATH

### Enable USB Debugging on Android Device

1. Go to **Settings** > **About Phone**
2. Tap **Build Number** 7 times to enable Developer Mode
3. Go to **Settings** > **Developer Options**
4. Enable **USB Debugging**

## 📥 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/zhangaina1200/AndroidAuto.git
cd AndroidAuto
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare APK Files

Place your APK files in the following directory structure:

```
AndroidAuto/
└── APK file/
    └── <version-folder>/
        ├── app1.apk
        ├── app2.apk
        └── ...
```

The tool will automatically detect and install APKs from the most recently modified folder.

## 🚀 Usage

### CLI Options

```bash
python main.py --info          # Get device info only
python main.py --screenshot    # Take screenshot only
python main.py --screenshot custom.png  # Take screenshot with custom filename
python main.py --install       # Install latest APK only
python main.py --all            # Run all functions
python main.py --help           # Show help message
```

| Option | Description |
|--------|-------------|
| `--info` | Retrieve and display device information |
| `--screenshot` | Capture device screen (default filename: screen.png) |
| `--install` | Install all APKs from the latest version folder |
| `--all` | Execute all functions (info, screenshot, install) |
| `--run <file>` | Run YAML configuration file |

---

### YAML Automation

Write automation scripts in YAML format and execute them:

```bash
python main.py --run test.yaml
```

**Example YAML file:**

```yaml
name: "Example Script"
devices:
  # serial: "device_serial"  # Optional

steps:
  - action: launch_app
    package: com.sportstracker

  - action: wait
    text: "开始运动"
    timeout: 10

  - action: tap
    text: "开始运动"

  - action: screenshot
    filename: "result.png"
```

#### Supported Actions

**App Management:**
| Action | Parameters |
|--------|------------|
| `launch_app` | `package` |
| `stop_app` | `package` |

**Touch Operations:**
| Action | Parameters |
|--------|------------|
| `tap` | `x, y` or `text` or `resource_id` or `class_name` |
| `double_tap` | `x, y` |
| `long_press` | `x, y` or `text` or `resource_id`, `duration` |
| `swipe` | `x1, y1, x2, y2, duration` |
| `swipe_up` | `distance` |
| `swipe_down` | `distance` |

**Text Input:**
| Action | Parameters |
|--------|------------|
| `input_text` | `text`, `text_match` or `resource_id`, `clear_first` |
| `clear_text` | `text` or `resource_id` |

**Key Operations:**
| Action | Parameters |
|--------|------------|
| `press_key` | `key` (back/home/power/volume_up/volume_down) |
| `press_back` | - |
| `press_home` | - |
| `press_power` | - |

**Wait Operations:**
| Action | Parameters |
|--------|------------|
| `wait` | `text` or `resource_id` or `class_name`, `timeout`, `exists` |
| `wait_time` | `seconds` |

**Screenshot:**
| Action | Parameters |
|--------|------------|
| `screenshot` | `filename` |

**Scroll Operations:**
| Action | Parameters |
|--------|------------|
| `scroll_up` | - |
| `scroll_down` | - |
| `scroll_to_text` | `text`, `max_swipe` |
| `scroll_to_resource_id` | `resource_id`, `max_swipe` |

**Assertions:**
| Action | Parameters |
|--------|------------|
| `assert_exists` | `text` or `resource_id` or `class_name` |
| `assert_text` | `expected`, `text` or `resource_id` |

#### Error Handling

When a step fails, the runner will:
1. Take a screenshot
2. Save error log to `run_YYYYMMDD_HHMMSS.log`
3. Continue executing remaining steps

### Connect Device

```python
from main import connect_device

device = connect_device()
print(f"Connected to: {device.serial}")
```

### Get Device Info

```python
from main import connect_device, get_device_info, print_device_info

device = connect_device()
info = get_device_info(device)
print_device_info(info)
```

Output:
```
========================================
设备信息
========================================
产品名称: Samsung Galaxy S21
Sdk版本: 31
屏幕分辨率: 2400 x 1080
当前应用: com.android.launcher
========================================
```

### Take Screenshot

```python
from main import take_screenshot

screenshot_file = take_screenshot("my_screenshot.png")
```

### Install APK

```python
from main import install_apk_files, get_latest_apk_folder

apk_folder = get_latest_apk_folder("path/to/APK file")
if apk_folder:
    success_count = install_apk_files(apk_folder)
    print(f"Installed {success_count} APKs")
```

## 📁 Project Structure

```
AndroidAuto/
├── main.py              # Main entry point
├── operations.py        # Core operation functions
├── runner.py            # YAML configuration runner
├── download_apk.py      # APK download tool
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
├── README.md            # This file
├── LICENSE              # MIT License
├── examples/            # Example YAML scripts
│   └── example_*.yaml
└── APK file/            # APK files directory
    └── <version>/
        ├── app.apk
        └── ...
```

## 📚 API Reference

### `connect_device()`
Connect to USB device.

**Returns:** `u2.Device` - UiAutomator2 device object

**Example:**
```python
device = connect_device()
```

---

### `get_device_info(device)`
Get device information.

**Parameters:**
- `device` (u2.Device): Device object from `connect_device()`

**Returns:** `dict` - Device information dictionary with keys:
- `productName`: Device model name
- `sdkInt`: Android SDK version
- `displayWidth`: Screen width in pixels
- `displayHeight`: Screen height in pixels
- `currentPackage`: Current running package name

**Example:**
```python
info = get_device_info(device)
print(info['productName'])  # "Samsung Galaxy S21"
```

---

### `print_device_info(info)`
Print device information in formatted style.

**Parameters:**
- `info` (dict): Device information from `get_device_info()`

---

### `take_screenshot(filename="screen.png")`
Capture screenshot and save to file.

**Parameters:**
- `filename` (str): Output filename (default: "screen.png")

**Returns:** `str` - Absolute path of saved file

---

### `get_latest_apk_folder(apk_base_path)`
Find the most recently modified subfolder.

**Parameters:**
- `apk_base_path` (str): Base directory containing version folders

**Returns:** `str` or `None` - Path to latest folder, or None if not found

---

### `install_apk_files(apk_folder_path)`
Install all APK files from a folder.

**Parameters:**
- `apk_folder_path` (str): Folder containing APK files

**Returns:** `int` - Number of successfully installed APKs

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please make sure to update tests as appropriate.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
