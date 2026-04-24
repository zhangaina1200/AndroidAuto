"""Tests for runner module"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch


class TestRunnerInit:
    """Test Runner class initialization."""

    def test_runner_sets_config_dir(self):
        """Test Runner sets config_dir from config_path."""
        from runner import Runner

        config_content = """
app: test_app
steps: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            assert runner.config_dir == os.path.dirname(os.path.abspath(config_path))
        finally:
            os.unlink(config_path)

    def test_runner_output_dir_structure(self):
        """Test output directory structure."""
        from runner import Runner

        config_content = """
app: my_app
steps: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            # output_dir structure: config_dir/screenshots/YYYY-MM-DD/my_app
            # parts = [..., "screenshots", "YYYY-MM-DD", "my_app"]
            parts = runner.output_dir.split(os.sep)
            # Last part should be app name
            assert parts[-1] == "my_app", f"Expected 'my_app', got '{parts[-1]}'"
            # Second to last should be date
            assert len(parts[-2]) == 10 and parts[-2][4] == '-' and parts[-2][7] == '-', f"Date format issue: {parts[-2]}"
            # Third to last should be screenshots
            assert parts[-3] == "screenshots", f"Expected 'screenshots', got '{parts[-3]}'"
        finally:
            os.unlink(config_path)

    def test_runner_device_serial_from_config(self):
        """Test device serial is read from config."""
        from runner import Runner

        config_content = """
devices:
  serial: test_device_123
steps: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            assert runner.device_serial == 'test_device_123'
        finally:
            os.unlink(config_path)

    def test_runner_device_serial_override(self):
        """Test device serial can be overridden."""
        from runner import Runner

        config_content = """
devices:
  serial: config_device
steps: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path, device_serial='override_device')
            assert runner.device_serial == 'override_device'
        finally:
            os.unlink(config_path)


class TestRunnerSteps:
    """Test Runner step execution."""

    def test_run_step_unknown_action(self):
        """Test unknown action logs error and returns False."""
        from runner import Runner

        config_content = """
steps:
  - action: unknown_action
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            runner.device = MagicMock()

            result = runner.run_step({'action': 'unknown_action'})

            assert result is False
            # Check error was logged
            error_logs = [log for log in runner.logs if 'ERROR' in log and 'unknown_action' in log]
            assert len(error_logs) > 0
        finally:
            os.unlink(config_path)

    @patch('runner.ops')
    def test_run_step_launch_app(self, mock_ops):
        """Test launch_app action."""
        from runner import Runner

        config_content = """
steps:
  - action: launch_app
    package: com.example.app
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            runner.device = MagicMock()
            mock_ops.launch_app.return_value = True

            result = runner.run_step({'action': 'launch_app', 'package': 'com.example.app'})

            assert result is True
            mock_ops.launch_app.assert_called_once()
        finally:
            os.unlink(config_path)

    @patch('runner.ops')
    def test_run_step_tap(self, mock_ops):
        """Test tap action."""
        from runner import Runner

        config_content = """
steps:
  - action: tap
    x: 100
    y: 200
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            runner.device = MagicMock()
            mock_ops.tap.return_value = True

            result = runner.run_step({'action': 'tap', 'x': 100, 'y': 200})

            assert result is True
            mock_ops.tap.assert_called_once_with(
                runner.device, x=100, y=200, text=None, resource_id=None, class_name=None, index=0
            )
        finally:
            os.unlink(config_path)

    @patch('runner.ops')
    def test_run_step_screenshot(self, mock_ops):
        """Test screenshot action."""
        from runner import Runner

        config_content = """
steps:
  - action: screenshot
    filename: test_screen.png
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            runner.device = MagicMock()
            mock_ops.screenshot.return_value = '/path/to/test_screen.png'

            result = runner.run_step({'action': 'screenshot', 'filename': 'test_screen.png'})

            assert result is True
            mock_ops.screenshot.assert_called_once()
        finally:
            os.unlink(config_path)


class TestRunnerLog:
    """Test Runner logging functionality."""

    def test_log_adds_timestamp(self):
        """Test log method adds timestamp."""
        from runner import Runner

        config_content = """
steps: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            runner.log("Test message")

            assert len(runner.logs) == 1
            assert "Test message" in runner.logs[0]
            assert "INFO" in runner.logs[0]
        finally:
            os.unlink(config_path)

    def test_error_logs_with_error_level(self):
        """Test error method logs with ERROR level."""
        from runner import Runner

        config_content = """
steps: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            runner = Runner(config_path)
            runner.error("Error message")

            assert len(runner.logs) == 1
            assert "ERROR" in runner.logs[0]
            assert "Error message" in runner.logs[0]
        finally:
            os.unlink(config_path)
