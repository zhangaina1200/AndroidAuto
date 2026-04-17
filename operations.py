"""
AndroidAuto Operations Module

Core operation functions for Android device automation.
"""
import uiautomator2 as u2
import os
import time
from PIL import Image


class Device:
    """Device wrapper for operations."""

    def __init__(self, serial=None):
        self.device = u2.connect(serial)
        self.serial = self.device.serial

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def connect(serial=None):
    """Connect to device."""
    return Device(serial)


# ============ App Management ============

def launch_app(device, package):
    """Launch an application by package name."""
    device.device.app_start(package)
    return True


def stop_app(device, package):
    """Stop an application by package name."""
    device.device.app_stop(package)
    return True


def get_current_app(device):
    """Get current running application package name."""
    return device.device.info.get('currentPackageName', None)


# ============ Touch Operations ============

def tap(device, x=None, y=None, text=None, resource_id=None, class_name=None, index=0):
    """Tap on coordinates or element."""
    if text:
        el = device.device(text=text)
        if index > 0:
            el = el[index]
        el.click()
    elif resource_id:
        el = device.device(resourceId=resource_id)
        if index > 0:
            el = el[index]
        el.click()
    elif class_name:
        el = device.device(className=class_name)
        if index > 0:
            el = el[index]
        el.click()
    else:
        device.device.click(x, y)
    return True


def double_tap(device, x=None, y=None):
    """Double tap on coordinates."""
    device.device.double_click(x, y)
    return True


def long_press(device, x=None, y=None, text=None, resource_id=None, duration=1.0):
    """Long press on coordinates or element."""
    if text:
        el = device.device(text=text)
        el.long_click(duration=duration)
    elif resource_id:
        el = device.device(resourceId=resource_id)
        el.long_click(duration=duration)
    else:
        device.device.long_click(x, y, duration=duration)
    return True


def swipe(device, x1, y1, x2, y2, duration=0.5):
    """Swipe from (x1, y1) to (x2, y2)."""
    device.device.swipe(x1, y1, x2, y2, duration=duration)
    return True


def swipe_up(device, distance=500, duration=0.5):
    """Swipe up on screen."""
    w, h = device.device.info['displayWidth'], device.device.info['displayHeight']
    device.device.swipe(w // 2, h * 3 // 4, w // 2, h // 4, duration=duration)


def swipe_down(device, distance=500, duration=0.5):
    """Swipe down on screen."""
    w, h = device.device.info['displayWidth'], device.device.info['displayHeight']
    device.device.swipe(w // 2, h // 4, w // 2, h * 3 // 4, duration=duration)


# ============ Text Input ============

def input_text(device, text, text_match=None, resource_id=None, clear_first=True):
    """Input text into element or current focused element."""
    if text_match:
        el = device.device(text=text_match)
        if clear_first:
            el.clear_text()
        el.set_text(text)
    elif resource_id:
        el = device.device(resourceId=resource_id)
        if clear_first:
            el.clear_text()
        el.set_text(text)
    else:
        device.device.set_fastinput_ime(True)
        device.device.send_keys(text)
        device.device.set_fastinput_ime(False)
    return True


def clear_text(device, text=None, resource_id=None):
    """Clear text from element."""
    if text:
        device.device(text=text).clear_text()
    elif resource_id:
        device.device(resourceId=resource_id).clear_text()
    return True


# ============ Key Operations ============

def press_key(device, key):
    """Press a key (back, home, power, etc.)."""
    key_map = {
        'back': 4,
        'home': 3,
        'power': 26,
        'volume_up': 24,
        'volume_down': 25,
        'menu': 82,
        'search': 84,
    }
    if isinstance(key, str):
        key = key_map.get(key.lower(), key)
    device.device.press(key)
    return True


def press_back(device):
    """Press back key."""
    return press_key(device, 'back')


def press_home(device):
    """Press home key."""
    return press_key(device, 'home')


def press_power(device):
    """Press power key."""
    return press_key(device, 'power')


# ============ Wait Operations ============

def wait(device, text=None, resource_id=None, class_name=None, timeout=10, exists=True):
    """
    Wait for element to appear or disappear.
    exists=True: wait for element to appear
    exists=False: wait for element to disappear
    """
    if text:
        if exists:
            device.device(text=text).wait(timeout=timeout)
        else:
            device.device(text=text).wait_gone(timeout=timeout)
    elif resource_id:
        if exists:
            device.device(resourceId=resource_id).wait(timeout=timeout)
        else:
            device.device(resourceId=resource_id).wait_gone(timeout=timeout)
    elif class_name:
        if exists:
            device.device(className=class_name).wait(timeout=timeout)
        else:
            device.device(className=class_name).wait_gone(timeout=timeout)
    else:
        time.sleep(timeout)
    return True


def wait_time(device, seconds):
    """Wait for specified seconds."""
    time.sleep(seconds)
    return True


# ============ Screenshot ============

def screenshot(device, filename="screen.png"):
    """Take screenshot and save to file."""
    img = device.device.screenshot()
    img.save(filename)
    return os.path.abspath(filename)


# ============ Scroll Operations ============

def scroll_up(device):
    """Scroll up (swipe down on screen)."""
    swipe_down(device)


def scroll_down(device):
    """Scroll down (swipe up on screen)."""
    swipe_up(device)


def scroll_to_text(device, text, max_swipe=10):
    """Scroll until specified text is found."""
    for _ in range(max_swipe):
        if device.device(text=text).exists():
            return True
        swipe_up(device)
    return False


def scroll_to_resource_id(device, resource_id, max_swipe=10):
    """Scroll until specified resource_id is found."""
    for _ in range(max_swipe):
        if device.device(resourceId=resource_id).exists():
            return True
        swipe_up(device)
    return False


# ============ Assertion Operations ============

def assert_exists(device, text=None, resource_id=None, class_name=None):
    """Assert element exists."""
    if text:
        assert device.device(text=text).exists(), f"Element not found: text={text}"
    elif resource_id:
        assert device.device(resourceId=resource_id).exists(), f"Element not found: resource_id={resource_id}"
    elif class_name:
        assert device.device(className=class_name).exists(), f"Element not found: class_name={class_name}"
    return True


def assert_text(device, expected_text, text=None, resource_id=None):
    """Assert element contains expected text."""
    if text:
        actual = device.device(text=text).get_text()
        assert actual == expected_text, f"Text mismatch: expected='{expected_text}', actual='{actual}'"
    elif resource_id:
        actual = device.device(resourceId=resource_id).get_text()
        assert actual == expected_text, f"Text mismatch: expected='{expected_text}', actual='{actual}'"
    return True


# ============ Element Info ============

def get_text(device, text=None, resource_id=None):
    """Get text from element."""
    if text:
        return device.device(text=text).get_text()
    elif resource_id:
        return device.device(resourceId=resource_id).get_text()
    return None


def exists(device, text=None, resource_id=None, class_name=None):
    """Check if element exists."""
    if text:
        return device.device(text=text).exists
    elif resource_id:
        return device.device(resourceId=resource_id).exists
    elif class_name:
        return device.device(className=class_name).exists
    return False
