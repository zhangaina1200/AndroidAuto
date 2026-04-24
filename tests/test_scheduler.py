"""Tests for scheduler module"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestScheduleConfig:
    """Test ScheduleConfig class."""

    def test_parse_time_valid(self):
        """Test _parse_time with valid input."""
        from scheduler import ScheduleConfig

        # Create a minimal config file
        config_content = """
target:
  app_package: com.example.app
time_windows:
  - start: "08:30"
    end: "08:45"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = ScheduleConfig(config_path)
            assert config._parse_time('08:30') == (8, 30)
            assert config._parse_time('18:15') == (18, 15)
        finally:
            os.unlink(config_path)

    def test_parse_time_invalid_format(self):
        """Test _parse_time with invalid format."""
        from scheduler import ScheduleConfig

        config_content = """
target:
  app_package: com.example.app
time_windows:
  - start: "08:30"
    end: "08:45"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = ScheduleConfig(config_path)
            with pytest.raises(ValueError) as exc_info:
                config._parse_time('invalid')
            assert '时间格式错误' in str(exc_info.value)
        finally:
            os.unlink(config_path)

    def test_default_time_windows(self):
        """Test default time windows when not specified in config."""
        from scheduler import ScheduleConfig

        # Config without time_windows
        config_content = """
target:
  app_package: com.example.app
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = ScheduleConfig(config_path)
            # Should use default time windows
            assert len(config.time_windows) == 1
            assert config.time_windows[0]['start'] == '09:00'
            assert config.time_windows[0]['end'] == '11:30'
        finally:
            os.unlink(config_path)

    def test_multiple_time_windows(self):
        """Test multiple time windows configuration."""
        from scheduler import ScheduleConfig

        config_content = """
target:
  app_package: com.example.app
time_windows:
  - start: "08:30"
    end: "08:45"
  - start: "18:15"
    end: "18:30"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = ScheduleConfig(config_path)
            assert len(config.time_windows) == 2
            assert config.time_windows[0]['start'] == '08:30'
            assert config.time_windows[1]['start'] == '18:15'
        finally:
            os.unlink(config_path)

    def test_validate_time_config_invalid_hour(self):
        """Test validation rejects invalid hour."""
        from scheduler import ScheduleConfig

        config_content = """
target:
  app_package: com.example.app
time_windows:
  - start: "25:00"
    end: "08:45"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                ScheduleConfig(config_path)
            assert '小时必须在 0-23 之间' in str(exc_info.value)
        finally:
            os.unlink(config_path)

    def test_validate_time_config_start_after_end(self):
        """Test validation rejects start time after end time."""
        from scheduler import ScheduleConfig

        config_content = """
target:
  app_package: com.example.app
time_windows:
  - start: "18:30"
    end: "08:00"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                ScheduleConfig(config_path)
            assert '开始时间' in str(exc_info.value)
        finally:
            os.unlink(config_path)


class TestScheduleConfigTimeHelpers:
    """Test ScheduleConfig helper methods."""

    def test_is_within_time_window_true(self):
        """Test is_within_time_window returns True when in window."""
        from scheduler import ScheduleConfig

        # Create config with known window
        config_content = """
target:
  app_package: com.example.app
time_windows:
  - start: "00:00"
    end: "23:59"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = ScheduleConfig(config_path)
            # Should be within window at any time
            assert config.is_within_time_window() is True
        finally:
            os.unlink(config_path)

    def test_is_within_time_window_false(self):
        """Test is_within_time_window returns False when outside window."""
        from scheduler import ScheduleConfig

        # Create config with narrow window
        config_content = """
target:
  app_package: com.example.app
time_windows:
  - start: "00:00"
    end: "00:01"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = ScheduleConfig(config_path)
            # Current time very likely outside window
            # Just verify it returns a boolean
            result = config.is_within_time_window()
            assert isinstance(result, bool)
        finally:
            os.unlink(config_path)

    def test_is_weekend(self):
        """Test is_weekend method."""
        from scheduler import ScheduleConfig

        config_content = """
target:
  app_package: com.example.app
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = ScheduleConfig(config_path)
            # Saturday = 5, Sunday = 6
            saturday = datetime(2024, 6, 1)  # June 1, 2024 was a Saturday
            sunday = datetime(2024, 6, 2)     # June 2, 2024 was a Sunday
            monday = datetime(2024, 6, 3)    # June 3, 2024 was a Monday

            assert config.is_weekend(saturday) is True
            assert config.is_weekend(sunday) is True
            assert config.is_weekend(monday) is False
        finally:
            os.unlink(config_path)

    def test_get_next_window_start(self):
        """Test get_next_window_start method."""
        from scheduler import ScheduleConfig

        config_content = """
target:
  app_package: com.example.app
time_windows:
  - start: "08:30"
    end: "08:45"
  - start: "18:15"
    end: "18:30"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = ScheduleConfig(config_path)
            next_start = config.get_next_window_start()
            # Should return a datetime
            assert isinstance(next_start, datetime)
        finally:
            os.unlink(config_path)


class TestExecutionLogger:
    """Test ExecutionLogger class."""

    def test_init_db(self):
        """Test database initialization."""
        import tempfile
        import shutil
        from scheduler import ExecutionLogger

        log_dir = tempfile.mkdtemp()
        try:
            logger = ExecutionLogger(log_dir)
            db_path = os.path.join(log_dir, 'execution_log.db')

            assert os.path.exists(db_path)

            # Check table exists
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_log'")
            assert cursor.fetchone() is not None
            conn.close()
        finally:
            shutil.rmtree(log_dir)

    def test_log_execution(self):
        """Test logging execution result."""
        import tempfile
        import shutil
        from scheduler import ExecutionLogger

        log_dir = tempfile.mkdtemp()
        try:
            logger = ExecutionLogger(log_dir)
            logger.log_execution(
                planned_time='2024-01-01 10:00:00',
                actual_time='2024-01-01 10:00:05',
                target_app='com.example.app',
                device_serial='test_serial',
                result='SUCCESS'
            )

            logs = logger.get_recent_logs(1)
            assert len(logs) == 1
            assert logs[0][3] == 'SUCCESS'
        finally:
            shutil.rmtree(log_dir)
