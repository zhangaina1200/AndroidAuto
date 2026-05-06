"""
AndroidAuto YAML Runner

Parse and execute YAML configuration files for Android automation.
"""
import os
import sys
import time
import yaml
import operations as ops


class StepError(Exception):
    """Exception raised when a step fails."""
    pass


class Runner:
    """YAML configuration runner."""

    def __init__(self, config_path, device_serial=None):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 从 config_path 推导配置目录，不再依赖 _file_path hack
        self.config_dir = os.path.dirname(os.path.abspath(config_path))

        # 如果是 suunto_cases 目录下的配置，改为输出到 reports 子目录
        if 'suunto_cases' in self.config_dir:
            self.config_dir = os.path.join(self.config_dir, 'reports')

        self.device_serial = device_serial or self.config.get('devices', {}).get('serial')
        self.device = None
        self.step_results = []
        self.logs = []
        self.output_dir = self._get_output_dir()

    def _get_output_dir(self):
        """Get structured output directory: screenshots/YYYY-MM-DD/app_name/"""
        date_str = time.strftime("%Y-%m-%d")
        # Determine app name from config or use 'general'
        app_name = self.config.get('app', 'general')
        output_dir = os.path.join(self.config_dir, "screenshots", date_str, app_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def connect_device(self):
        """Connect to device."""
        self.device = ops.connect_with_retry(self.device_serial)
        self.log(f"Connected to device: {self.device.serial}")

    def log(self, message, level="INFO"):
        """Log a message."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def error(self, message):
        """Log an error message."""
        self.log(message, level="ERROR")

    def save_screenshot(self, filename):
        """Save screenshot to structured directory and add to logs."""
        if self.device:
            # Use structured output directory
            path = os.path.join(self.output_dir, filename)
            ops.screenshot(self.device, path)
            self.log(f"Screenshot saved: {path}")
            return path
        return None

    def handle_error(self, step, e):
        """Handle step execution error."""
        self.error(f"Step failed: {step.get('action', 'unknown')}")
        self.error(f"Error: {str(e)}")

        # Save screenshot to error subdirectory
        error_dir = os.path.join(self.output_dir, "errors")
        os.makedirs(error_dir, exist_ok=True)
        screenshot_name = f"error_{time.strftime('%Y%m%d_%H%M%S')}.png"
        error_path = os.path.join(error_dir, screenshot_name)
        ops.screenshot(self.device, error_path)
        self.log(f"Error screenshot saved: {error_path}")

        # Continue execution
        self.log("Continuing execution...")
        return True

    def run_step(self, step):
        """Execute a single step."""
        action = step.get('action')
        self.log(f"Executing: {action}")

        try:
            if action == 'launch_app':
                return ops.launch_app(self.device, step['package'])

            elif action == 'stop_app':
                return ops.stop_app(self.device, step['package'])

            elif action == 'get_current_app':
                pkg = ops.get_current_app(self.device)
                self.log(f"Current app: {pkg}")
                return True

            elif action == 'tap':
                return ops.tap(
                    self.device,
                    x=step.get('x'),
                    y=step.get('y'),
                    text=step.get('text'),
                    resource_id=step.get('resource_id'),
                    class_name=step.get('class_name'),
                    index=step.get('index', 0)
                )

            elif action == 'double_tap':
                return ops.double_tap(self.device, step['x'], step['y'])

            elif action == 'long_press':
                return ops.long_press(
                    self.device,
                    x=step.get('x'),
                    y=step.get('y'),
                    text=step.get('text'),
                    resource_id=step.get('resource_id'),
                    duration=step.get('duration', 1.0)
                )

            elif action == 'swipe':
                return ops.swipe(
                    self.device,
                    step['x1'], step['y1'],
                    step['x2'], step['y2'],
                    step.get('duration', 0.5)
                )

            elif action == 'swipe_up':
                return ops.swipe_up(self.device, step.get('distance', 500))

            elif action == 'swipe_down':
                return ops.swipe_down(self.device, step.get('distance', 500))

            elif action == 'swipe_left':
                return ops.swipe_left(self.device, step.get('distance', 500))

            elif action == 'swipe_right':
                return ops.swipe_right(self.device, step.get('distance', 500))

            elif action == 'input_text':
                return ops.input_text(
                    self.device,
                    step['text'],
                    text_match=step.get('text_match'),
                    resource_id=step.get('resource_id'),
                    clear_first=step.get('clear_first', True)
                )

            elif action == 'clear_text':
                return ops.clear_text(
                    self.device,
                    text=step.get('text'),
                    resource_id=step.get('resource_id')
                )

            elif action == 'press_key':
                return ops.press_key(self.device, step['key'])

            elif action == 'press_back':
                return ops.press_back(self.device)

            elif action == 'press_home':
                return ops.press_home(self.device)

            elif action == 'press_power':
                return ops.press_power(self.device)

            elif action == 'wait':
                return ops.wait(
                    self.device,
                    text=step.get('text'),
                    resource_id=step.get('resource_id'),
                    class_name=step.get('class_name'),
                    timeout=step.get('timeout', 10),
                    exists=step.get('exists', True)
                )

            elif action == 'wait_time':
                return ops.wait_time(self.device, step['seconds'])

            elif action == 'screenshot':
                filename = step.get('filename', 'screen.png')
                self.save_screenshot(filename)
                return True

            elif action == 'scroll_up':
                return ops.scroll_up(self.device)

            elif action == 'scroll_down':
                return ops.scroll_down(self.device)

            elif action == 'scroll_to_text':
                return ops.scroll_to_text(
                    self.device,
                    step['text'],
                    step.get('max_swipe', 10)
                )

            elif action == 'scroll_to_resource_id':
                return ops.scroll_to_resource_id(
                    self.device,
                    step['resource_id'],
                    step.get('max_swipe', 10)
                )

            elif action == 'assert_exists':
                return ops.assert_exists(
                    self.device,
                    text=step.get('text'),
                    resource_id=step.get('resource_id'),
                    class_name=step.get('class_name')
                )

            elif action == 'assert_text':
                return ops.assert_text(
                    self.device,
                    step['expected'],
                    text=step.get('text'),
                    resource_id=step.get('resource_id')
                )

            else:
                self.error(f"Unknown action: {action}")
                return False

        except Exception as e:
            self.handle_error(step, e)
            return False

    def run(self):
        """Run all steps in the configuration."""
        self.connect_device()

        steps = self.config.get('steps', [])
        self.log(f"Starting {len(steps)} steps...")

        success_count = 0
        fail_count = 0

        for i, step in enumerate(steps, 1):
            self.log(f"--- Step {i}/{len(steps)} ---")
            result = self.run_step(step)
            if result:
                success_count += 1
            else:
                fail_count += 1

        # Save log
        log_path = self.save_log()

        # Summary
        self.log("=" * 50)
        self.log(f"Execution completed: {success_count} succeeded, {fail_count} failed")
        if log_path:
            self.log(f"Log saved: {log_path}")

        return success_count, fail_count

    def save_log(self):
        """Save execution log to file in logs subdirectory."""
        log_dir = os.path.join(self.config_dir, "screenshots", time.strftime("%Y-%m-%d"), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"run_{time.strftime('%Y%m%d_%H%M%S')}.log")

        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.logs))

        return log_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description='AndroidAuto YAML Runner')
    parser.add_argument('config', help='Path to YAML configuration file')
    parser.add_argument('--serial', '-s', help='Device serial number (overrides config)')

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    runner = Runner(args.config, args.serial)
    runner.run()


if __name__ == "__main__":
    main()
