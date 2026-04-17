"""
APK Download and Organize Tool

Download APK files and organize them into version-matched folders.
Usage: python download_apk.py <apk_link> [apk_link2 ...]
"""
import os
import re
import sys
import urllib.request
import urllib.error


def extract_version_from_link(link):
    """
    Extract version string from APK download link.
    Example: https://mobile-tc-eu.s3.amazonaws.com/sportstracker/6_9_2/sportstracker-playstore-release-6_9_2-307.apk
             -> 6.9.2-307
    """
    # Pattern to find version like x_x_x-xxx or x.x.x-xxx
    # Matches: 6_9_2-307, 6.9.2-307, 10_0_0-123, etc.
    pattern = r'(\d+[._]\d+[._]\d+-\d+)'
    match = re.search(pattern, link)

    if not match:
        return None

    version_raw = match.group(1)
    # Normalize: convert underscores to dots
    version = version_raw.replace('_', '.')
    return version


def get_filename_from_link(link):
    """Extract filename from URL."""
    return os.path.basename(link.split('?')[0])


def download_apk(link, dest_folder):
    """Download APK file from link to destination folder."""
    filename = get_filename_from_link(link)
    filepath = os.path.join(dest_folder, filename)

    print(f"Downloading: {filename}")
    print(f"From: {link}")

    try:
        urllib.request.urlretrieve(link, filepath)
        print(f"Saved to: {filepath}")
        return filepath
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"Download failed: {str(e)}")
        return None


def organize_apk(link, base_path="APK file"):
    """
    Download APK and organize into version-matched folder.

    Args:
        link: APK download URL
        base_path: Base folder for APK storage (default: "APK file")

    Returns:
        tuple: (version_folder_path, downloaded_filename) or (None, None) if failed
    """
    version = extract_version_from_link(link)

    if not version:
        print(f"Failed to extract version from link: {link}")
        return None, None

    # Create version folder
    version_folder = os.path.join(base_path, version)
    os.makedirs(version_folder, exist_ok=True)

    # Download APK to version folder
    filename = get_filename_from_link(link)
    filepath = os.path.join(version_folder, filename)

    if os.path.exists(filepath):
        print(f"File already exists: {filepath}")
        return version_folder, filename

    downloaded = download_apk(link, version_folder)
    if downloaded:
        return version_folder, os.path.basename(downloaded)

    return None, None


def main():
    if len(sys.argv) < 2:
        print("Usage: python download_apk.py <apk_link> [apk_link2 ...]")
        print("\nExample:")
        print('  python download_apk.py "https://mobile-tc-eu.s3.amazonaws.com/sportstracker/6_9_2/sportstracker-playstore-release-6_9_2-307.apk"')
        sys.exit(1)

    links = sys.argv[1:]
    base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "APK file")

    print(f"Base APK folder: {os.path.abspath(base_path)}")
    print(f"Processing {len(links)} link(s)...\n")

    results = []
    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}] Processing: {link}")
        version_folder, filename = organize_apk(link, base_path)
        if version_folder:
            results.append((version_folder, filename))
            print(f"Success: {version_folder}\n")
        else:
            print(f"Failed!\n")

    # Summary
    print("=" * 50)
    print(f"Completed: {len(results)}/{len(links)} succeeded")

    if results:
        print("\nDownloaded files:")
        for folder, filename in results:
            print(f"  - {os.path.join(folder, filename)}")


if __name__ == "__main__":
    main()
