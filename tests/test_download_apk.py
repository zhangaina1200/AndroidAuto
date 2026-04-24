"""Tests for download_apk module"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock


class TestExtractVersionFromLink:
    """Test extract_version_from_link function."""

    def test_extract_version_underscore_format(self):
        """Test extracting version from underscore format link."""
        from download_apk import extract_version_from_link

        link = "https://mobile-tc-eu.s3.amazonaws.com/sportstracker/6_9_2/sportstracker-playstore-release-6_9_2-307.apk"
        version = extract_version_from_link(link)

        assert version == "6.9.2-307"

    def test_extract_version_dot_format(self):
        """Test extracting version from dot format link."""
        from download_apk import extract_version_from_link

        link = "https://example.com/app/10.0.0-123/app-10.0.0-123.apk"
        version = extract_version_from_link(link)

        assert version == "10.0.0-123"

    def test_extract_version_no_match(self):
        """Test extract_version_from_link returns None when no version found."""
        from download_apk import extract_version_from_link

        link = "https://example.com/app/latest/app.apk"
        version = extract_version_from_link(link)

        assert version is None

    def test_extract_version_complex_version(self):
        """Test extracting complex version string."""
        from download_apk import extract_version_from_link

        link = "https://example.com/app/1_2_3-999/app-1_2_3-999.apk"
        version = extract_version_from_link(link)

        # Pattern \d+[._]\d+[._]\d+-\d+ matches 1_2_3-999
        assert version == "1.2.3-999"


class TestGetFilenameFromLink:
    """Test get_filename_from_link function."""

    def test_get_filename_simple(self):
        """Test extracting filename from simple URL."""
        from download_apk import get_filename_from_link

        link = "https://example.com/apk/app.apk"
        filename = get_filename_from_link(link)

        assert filename == "app.apk"

    def test_get_filename_with_query_params(self):
        """Test extracting filename from URL with query parameters."""
        from download_apk import get_filename_from_link

        link = "https://example.com/apk/app.apk?token=abc123"
        filename = get_filename_from_link(link)

        assert filename == "app.apk"


class TestOrganizeApk:
    """Test organize_apk function."""

    @patch('download_apk.download_apk')
    def test_organize_apk_extracts_version(self, mock_download):
        """Test organize_apk extracts version and creates folder."""
        from download_apk import organize_apk

        base_path = tempfile.mkdtemp()
        link = "https://example.com/6_9_2/app-6_9_2-307.apk"
        mock_download.return_value = os.path.join(base_path, "6.9.2-307", "app-6_9_2-307.apk")

        try:
            version_folder, filename = organize_apk(link, base_path)

            assert version_folder == os.path.join(base_path, "6.9.2-307")
            assert filename == "app-6_9_2-307.apk"
        finally:
            shutil.rmtree(base_path)

    def test_organize_apk_no_version(self):
        """Test organize_apk returns None when no version found."""
        from download_apk import organize_apk

        base_path = tempfile.mkdtemp()
        link = "https://example.com/latest/app.apk"

        try:
            version_folder, filename = organize_apk(link, base_path)

            assert version_folder is None
            assert filename is None
        finally:
            shutil.rmtree(base_path)

    @patch('download_apk.download_apk')
    def test_organize_apk_skips_existing(self, mock_download):
        """Test organize_apk skips download if file exists."""
        from download_apk import organize_apk

        base_path = tempfile.mkdtemp()
        link = "https://example.com/1_0_0/app-1_0_0-1.apk"

        # Pre-create the file
        version_folder = os.path.join(base_path, "1.0.0-1")
        os.makedirs(version_folder)
        existing_file = os.path.join(version_folder, "app-1_0_0-1.apk")
        with open(existing_file, 'w') as f:
            f.write("existing")

        try:
            version_folder_result, filename = organize_apk(link, base_path)

            assert version_folder_result == os.path.join(base_path, "1.0.0-1")
            assert filename == "app-1_0_0-1.apk"
            # download_apk should not be called since file exists
            mock_download.assert_not_called()
        finally:
            shutil.rmtree(base_path)


class TestDownloadApk:
    """Test download_apk function."""

    @patch('urllib.request.urlretrieve')
    def test_download_apk_success(self, mock_retrieve):
        """Test successful APK download."""
        from download_apk import download_apk
        import os

        mock_retrieve.return_value = (None, None)  # urlretrieve returns (filename, headers)

        result = download_apk("https://example.com/app.apk", "/tmp")

        assert os.path.normpath(result) == os.path.normpath("/tmp/app.apk")
        mock_retrieve.assert_called_once()

    @patch('urllib.request.urlretrieve')
    def test_download_apk_http_error(self, mock_retrieve):
        """Test download handles HTTP error."""
        from download_apk import download_apk
        import urllib.error

        mock_retrieve.side_effect = urllib.error.HTTPError(
            url="https://example.com/app.apk",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )

        result = download_apk("https://example.com/app.apk", "/tmp")

        assert result is None

    @patch('urllib.request.urlretrieve')
    def test_download_apk_url_error(self, mock_retrieve):
        """Test download handles URL error."""
        from download_apk import download_apk
        import urllib.error

        mock_retrieve.side_effect = urllib.error.URLError("Connection refused")

        result = download_apk("https://example.com/app.apk", "/tmp")

        assert result is None
