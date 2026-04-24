"""Tests for device module"""
import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch


class TestConnectDevice:
    """Test connect_device function."""

    @patch('device.u2')
    @patch('device.time')
    def test_connect_device_success_first_try(self, mock_time, mock_u2):
        """Test successful connection on first attempt."""
        from device import connect_device

        mock_device = MagicMock()
        mock_device.info = {}  # Verify connection
        mock_u2.connect.return_value = mock_device

        result = connect_device(serial=None, max_retries=3, retry_interval=5)

        assert result == mock_device
        mock_u2.connect.assert_called_once_with(None)
        mock_time.sleep.assert_not_called()

    @patch('device.u2')
    @patch('device.time')
    def test_connect_device_success_after_retries(self, mock_time, mock_u2):
        """Test successful connection after initial failures."""
        from device import connect_device

        mock_device = MagicMock()
        mock_device.info = {}
        # First two calls raise, third succeeds
        mock_u2.connect.side_effect = [Exception("fail"), Exception("fail"), mock_device]

        result = connect_device(serial='test_serial', max_retries=3, retry_interval=5)

        assert result == mock_device
        assert mock_u2.connect.call_count == 3
        assert mock_time.sleep.call_count == 2

    @patch('device.u2')
    @patch('device.time')
    def test_connect_device_all_retries_fail(self, mock_time, mock_u2):
        """Test connection failure after max retries."""
        from device import connect_device

        mock_u2.connect.side_effect = Exception("connection refused")

        with pytest.raises(Exception) as exc_info:
            connect_device(serial=None, max_retries=3, retry_interval=5)

        assert "connection refused" in str(exc_info.value)
        assert mock_u2.connect.call_count == 3
        assert mock_time.sleep.call_count == 2

    @patch('device.u2')
    def test_connect_device_with_serial(self, mock_u2):
        """Test connection with specific serial number."""
        from device import connect_device

        mock_device = MagicMock()
        mock_device.info = {}
        mock_u2.connect.return_value = mock_device

        result = connect_device(serial='ABC123', max_retries=1, retry_interval=1)

        mock_u2.connect.assert_called_once_with('ABC123')


class TestGetDeviceInfo:
    """Test get_device_info function."""

    def test_get_device_info_all_fields(self):
        """Test get_device_info returns all expected fields."""
        from device import get_device_info

        mock_device = MagicMock()
        mock_device.info = {
            'productName': 'TestPhone',
            'sdkInt': 30,
            'displayWidth': 1080,
            'displayHeight': 1920,
            'currentPackageName': 'com.example.app'
        }

        result = get_device_info(mock_device)

        assert result['productName'] == 'TestPhone'
        assert result['sdkInt'] == 30
        assert result['displayWidth'] == 1080
        assert result['displayHeight'] == 1920
        assert result['currentPackage'] == 'com.example.app'

    def test_get_device_info_missing_fields(self):
        """Test get_device_info handles missing fields."""
        from device import get_device_info

        mock_device = MagicMock()
        mock_device.info = {}

        result = get_device_info(mock_device)

        assert result['productName'] == 'Unknown'
        assert result['sdkInt'] == 'Unknown'
        assert result['displayWidth'] == 'Unknown'
        assert result['displayHeight'] == 'Unknown'
        assert result['currentPackage'] == 'Unknown'


class TestTakeScreenshot:
    """Test take_screenshot function."""

    @patch('device.os.path.abspath')
    def test_take_screenshot(self, mock_abspath):
        """Test screenshot is saved correctly."""
        from device import take_screenshot

        mock_device = MagicMock()
        mock_image = MagicMock()
        mock_device.screenshot.return_value = mock_image
        mock_abspath.return_value = '/path/to/screen.png'

        result = take_screenshot(mock_device, filename='screen.png')

        mock_device.screenshot.assert_called_once()
        mock_image.save.assert_called_once_with('screen.png')
        assert result == '/path/to/screen.png'
