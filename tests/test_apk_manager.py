"""Tests for apk_manager module"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock


class TestGetLatestApkFolder:
    """Test get_latest_apk_folder function."""

    def test_get_latest_apk_folder_finds_latest(self):
        """Test finds the most recently modified folder."""
        from apk_manager import get_latest_apk_folder

        base_path = tempfile.mkdtemp()
        try:
            # Create folders with different modification times
            old_folder = os.path.join(base_path, "1.0.0")
            new_folder = os.path.join(base_path, "2.0.0")
            os.makedirs(old_folder)
            os.makedirs(new_folder)

            # Make new_folder more recent by updating mtime
            import time
            time.sleep(0.1)
            os.utime(new_folder, None)

            result = get_latest_apk_folder(base_path)

            assert result == new_folder
        finally:
            shutil.rmtree(base_path)

    def test_get_latest_apk_folder_none_exist(self):
        """Test returns None when no folders exist."""
        from apk_manager import get_latest_apk_folder

        base_path = tempfile.mkdtemp()
        try:
            result = get_latest_apk_folder(base_path)

            assert result is None
        finally:
            shutil.rmtree(base_path)

    def test_get_latest_apk_folder_path_not_exist(self):
        """Test returns None when base path doesn't exist."""
        from apk_manager import get_latest_apk_folder

        result = get_latest_apk_folder("/nonexistent/path")

        assert result is None

    def test_get_latest_apk_folder_with_files_only(self):
        """Test ignores files and only considers directories."""
        from apk_manager import get_latest_apk_folder

        base_path = tempfile.mkdtemp()
        try:
            # Create a folder and a file
            folder = os.path.join(base_path, "1.0.0")
            os.makedirs(folder)
            with open(os.path.join(base_path, "readme.txt"), 'w') as f:
                f.write("readme")

            result = get_latest_apk_folder(base_path)

            assert result == folder
        finally:
            shutil.rmtree(base_path)


class TestInstallApkFiles:
    """Test install_apk_files function."""

    def test_install_apk_files_invalid_folder(self):
        """Test returns 0 for invalid folder path."""
        from apk_manager import install_apk_files

        result = install_apk_files("/nonexistent/folder")

        assert result == 0

    def test_install_apk_files_no_apk_files(self):
        """Test returns 0 when no APK files found."""
        from apk_manager import install_apk_files

        base_path = tempfile.mkdtemp()
        try:
            result = install_apk_files(base_path)

            assert result == 0
        finally:
            shutil.rmtree(base_path)

    @patch('apk_manager.subprocess.run')
    def test_install_apk_files_success(self, mock_run):
        """Test successful APK installation."""
        from apk_manager import install_apk_files

        base_path = tempfile.mkdtemp()
        try:
            # Create a test APK file
            apk_path = os.path.join(base_path, "test.apk")
            with open(apk_path, 'w') as f:
                f.write("fake apk")

            # Mock subprocess.run success
            mock_run.return_value = MagicMock(returncode=0, stderr='')

            result = install_apk_files(base_path, device_serial='test_serial')

            assert result == 1
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert 'adb' in args
            assert 'install' in args
            assert '-r' in args
        finally:
            shutil.rmtree(base_path)

    @patch('apk_manager.subprocess.run')
    def test_install_apk_files_partial_failure(self, mock_run):
        """Test partial installation success."""
        from apk_manager import install_apk_files

        base_path = tempfile.mkdtemp()
        try:
            # Create two APK files
            apk1 = os.path.join(base_path, "app1.apk")
            apk2 = os.path.join(base_path, "app2.apk")
            with open(apk1, 'w') as f:
                f.write("fake apk1")
            with open(apk2, 'w') as f:
                f.write("fake apk2")

            # First install succeeds, second fails
            mock_run.side_effect = [
                MagicMock(returncode=0, stderr=''),
                MagicMock(returncode=1, stderr='Installation failed')
            ]

            result = install_apk_files(base_path, device_serial='test_serial')

            assert result == 1  # Only one succeeded
        finally:
            shutil.rmtree(base_path)

    @patch('apk_manager.subprocess.run')
    def test_install_apk_files_with_serial(self, mock_run):
        """Test installation with specified device serial."""
        from apk_manager import install_apk_files

        base_path = tempfile.mkdtemp()
        try:
            apk_path = os.path.join(base_path, "test.apk")
            with open(apk_path, 'w') as f:
                f.write("fake apk")

            mock_run.return_value = MagicMock(returncode=0, stderr='')

            result = install_apk_files(base_path, device_serial='specific_serial')

            assert result == 1
            args = mock_run.call_args[0][0]
            assert '-s' in args
            assert 'specific_serial' in args
        finally:
            shutil.rmtree(base_path)


class TestInstallLatest:
    """Test install_latest function."""

    @patch('apk_manager.get_latest_apk_folder')
    @patch('apk_manager.install_apk_files')
    def test_install_latest_no_folder(self, mock_install, mock_get_latest):
        """Test install_latest when no APK folder found."""
        from apk_manager import install_latest

        mock_get_latest.return_value = None

        result = install_latest()

        assert result == 0
        mock_install.assert_not_called()

    @patch('apk_manager.get_latest_apk_folder')
    @patch('apk_manager.install_apk_files')
    def test_install_latest_success(self, mock_install, mock_get_latest):
        """Test successful installation."""
        from apk_manager import install_latest

        mock_get_latest.return_value = '/path/to/latest'
        mock_install.return_value = 3

        result = install_latest()

        assert result == 3
        mock_get_latest.assert_called_once()
        mock_install.assert_called_once_with('/path/to/latest')


class TestVersionValidation:
    """Test version format validation."""

    def test_is_valid_version_format_valid(self):
        """Test valid version formats."""
        from apk_manager import is_valid_version_format

        assert is_valid_version_format("1.0.0-1") is True
        assert is_valid_version_format("1.2.3-456") is True
        assert is_valid_version_format("10.20.30-999") is True

    def test_is_valid_version_format_invalid(self):
        """Test invalid version formats."""
        from apk_manager import is_valid_version_format

        assert is_valid_version_format("1.0.0") is False  # missing build number
        assert is_valid_version_format("1.0-1") is False   # only 2 parts
        assert is_valid_version_format("v1.0.0-1") is False  # has letter
        assert is_valid_version_format("latest") is False   # text
        assert is_valid_version_format("") is False        # empty


class TestListAvailableVersions:
    """Test list_available_versions function."""

    def test_list_available_versions(self):
        """Test listing available versions."""
        from apk_manager import list_available_versions

        base_path = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(base_path, "1.0.0"))
            os.makedirs(os.path.join(base_path, "2.0.0"))
            os.makedirs(os.path.join(base_path, "3.0.0"))

            versions = list_available_versions(base_path)

            assert len(versions) == 3
            assert "3.0.0" in versions
            assert "2.0.0" in versions
            assert "1.0.0" in versions
        finally:
            shutil.rmtree(base_path)

    def test_list_available_versions_empty(self):
        """Test listing when no versions exist."""
        from apk_manager import list_available_versions

        base_path = tempfile.mkdtemp()
        try:
            versions = list_available_versions(base_path)
            assert versions == []
        finally:
            shutil.rmtree(base_path)


class TestGetApkFolderByVersion:
    """Test get_apk_folder_by_version function."""

    def test_get_apk_folder_by_version_exists(self):
        """Test getting folder that exists."""
        from apk_manager import get_apk_folder_by_version

        base_path = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(base_path, "1.2.3-456"))

            result = get_apk_folder_by_version("1.2.3-456", base_path)

            assert result == os.path.join(base_path, "1.2.3-456")
        finally:
            shutil.rmtree(base_path)

    def test_get_apk_folder_by_version_not_exists(self):
        """Test getting folder that doesn't exist."""
        from apk_manager import get_apk_folder_by_version

        base_path = tempfile.mkdtemp()
        try:
            result = get_apk_folder_by_version("9.9.9-999", base_path)

            assert result is None
        finally:
            shutil.rmtree(base_path)


class TestInstallByVersion:
    """Test install_by_version function."""

    @patch('apk_manager.install_apk_files')
    def test_install_by_version_success(self, mock_install):
        """Test successful installation of specific version."""
        from apk_manager import install_by_version

        base_path = tempfile.mkdtemp()
        try:
            version_folder = os.path.join(base_path, "1.2.3-456")
            os.makedirs(version_folder)
            with open(os.path.join(version_folder, "app.apk"), 'w') as f:
                f.write("fake apk")

            mock_install.return_value = 1

            result = install_by_version("1.2.3-456", base_path)

            assert result == 1
            mock_install.assert_called_once()
        finally:
            shutil.rmtree(base_path)

    def test_install_by_version_invalid_format(self):
        """Test install with invalid version format."""
        from apk_manager import install_by_version

        base_path = tempfile.mkdtemp()
        try:
            result = install_by_version("invalid", base_path)

            assert result == -1
        finally:
            shutil.rmtree(base_path)

    def test_install_by_version_not_exists(self):
        """Test install when version doesn't exist."""
        from apk_manager import install_by_version

        base_path = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(base_path, "1.0.0-1"))

            result = install_by_version("9.9.9-999", base_path)

            assert result == -1
        finally:
            shutil.rmtree(base_path)

    def test_install_by_version_no_apk_files(self):
        """Test install when version folder has no APK files."""
        from apk_manager import install_by_version

        base_path = tempfile.mkdtemp()
        try:
            version_folder = os.path.join(base_path, "1.0.0-1")
            os.makedirs(version_folder)
            with open(os.path.join(version_folder, "readme.txt"), 'w') as f:
                f.write("readme")

            result = install_by_version("1.0.0-1", base_path)

            assert result == -1
        finally:
            shutil.rmtree(base_path)
