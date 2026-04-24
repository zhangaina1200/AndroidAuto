"""Tests for operations module"""
import pytest
from unittest.mock import MagicMock, patch


class TestConnect:
    """Test device connection functions."""

    @patch('operations.u2')
    def test_connect_without_serial(self, mock_u2):
        """Test connect without serial (auto-detect)."""
        from operations import connect

        mock_device = MagicMock()
        mock_u2.connect.return_value = mock_device

        result = connect()

        mock_u2.connect.assert_called_once_with(None)
        assert result.device == mock_device
        assert result.serial == mock_device.serial

    @patch('operations.u2')
    def test_connect_with_serial(self, mock_u2):
        """Test connect with specific serial."""
        from operations import connect

        mock_device = MagicMock()
        mock_device.serial = '12345'
        mock_u2.connect.return_value = mock_device

        result = connect(serial='12345')

        mock_u2.connect.assert_called_once_with('12345')
        assert result.serial == '12345'


class TestConnectWithRetry:
    """Test connect_with_retry function."""

    @patch('operations.Device')
    def test_connect_with_retry_success_first_try(self, mock_device_class):
        """Test successful connection on first attempt."""
        from operations import connect_with_retry

        mock_device = MagicMock()
        mock_device.device.info = {}
        mock_device_class.return_value = mock_device

        result = connect_with_retry(serial='test_serial', max_retries=3, retry_interval=5)

        assert result == mock_device
        mock_device_class.assert_called_once_with('test_serial')

    @patch('time.sleep', return_value=None)
    @patch('operations.Device')
    def test_connect_with_retry_success_after_failures(self, mock_device_class, mock_sleep):
        """Test successful connection after initial failures."""
        from operations import connect_with_retry

        mock_device = MagicMock()
        mock_device.device.info = {}
        # First two calls raise, third succeeds
        mock_device_class.side_effect = [Exception("fail"), Exception("fail"), mock_device]

        result = connect_with_retry(serial='test_serial', max_retries=3, retry_interval=5)

        assert result == mock_device
        assert mock_device_class.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('time.sleep', return_value=None)
    @patch('operations.Device')
    def test_connect_with_retry_all_fail(self, mock_device_class, mock_sleep):
        """Test connection failure after max retries."""
        from operations import connect_with_retry

        mock_device_class.side_effect = Exception("connection failed")

        with pytest.raises(Exception) as exc_info:
            connect_with_retry(serial='test_serial', max_retries=3, retry_interval=5)

        assert "connection failed" in str(exc_info.value)
        assert mock_device_class.call_count == 3
        assert mock_sleep.call_count == 2


class TestTap:
    """Test tap function."""

    @patch('operations.Device')
    def test_tap_by_coordinates(self, mock_device_class):
        """Test tap by x, y coordinates."""
        from operations import tap

        mock_device = MagicMock()
        mock_device.device.click = MagicMock()
        mock_device_class.return_value = mock_device

        result = tap(mock_device, x=100, y=200)

        assert result is True
        mock_device.device.click.assert_called_once_with(100, 200)

    @patch('operations.Device')
    def test_tap_by_text(self, mock_device_class):
        """Test tap by text."""
        from operations import tap

        mock_device = MagicMock()
        mock_element = MagicMock()
        mock_device.device.return_value = mock_element
        mock_device_class.return_value = mock_device

        result = tap(mock_device, text="Button")

        mock_device.device.assert_called_with(text="Button")
        mock_element.click.assert_called_once()

    @patch('operations.Device')
    def test_tap_by_resource_id(self, mock_device_class):
        """Test tap by resource_id."""
        from operations import tap

        mock_device = MagicMock()
        mock_element = MagicMock()
        mock_device.device.return_value = mock_element
        mock_device_class.return_value = mock_device

        result = tap(mock_device, resource_id="com.example:id/button")

        mock_device.device.assert_called_with(resourceId="com.example:id/button")
        mock_element.click.assert_called_once()

    @patch('operations.Device')
    def test_tap_with_index(self, mock_device_class):
        """Test tap with index parameter."""
        from operations import tap

        mock_device = MagicMock()
        mock_element = MagicMock()
        mock_device.device.return_value = mock_element
        mock_device_class.return_value = mock_device

        result = tap(mock_device, text="Item", index=2)

        mock_device.device.assert_called_with(text="Item")
        mock_element.__getitem__.assert_called_with(2)
        mock_element[2].click.assert_called_once()
