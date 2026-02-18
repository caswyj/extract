"""
Cross-platform hotkey management using pynput.
"""

import threading
from typing import Callable, Dict, Optional

from ..platform.base import PlatformManager


class HotkeyManager:
    """
    Cross-platform hotkey manager that wraps platform-specific implementations.
    """

    def __init__(self):
        """Initialize the hotkey manager."""
        self._platform_manager = PlatformManager.get_hotkey_manager()
        self._callbacks: Dict[str, Callable[[], None]] = {}

    def register(self, hotkey: str, callback: Callable[[], None]) -> bool:
        """
        Register a global hotkey.

        Args:
            hotkey: Hotkey string (e.g., "ctrl+shift+o", "cmd+shift+o").
                   Platform-specific modifiers:
                   - Windows/Linux: ctrl, alt, shift, win
                   - macOS: ctrl, alt/option, shift, cmd/command
            callback: Function to call when hotkey is pressed.

        Returns:
            True if registration successful, False otherwise.
        """
        self._callbacks[hotkey] = callback
        return self._platform_manager.register(hotkey, callback)

    def unregister(self, hotkey: str) -> bool:
        """
        Unregister a previously registered hotkey.

        Args:
            hotkey: The hotkey string to unregister.

        Returns:
            True if unregistration successful, False otherwise.
        """
        if hotkey in self._callbacks:
            del self._callbacks[hotkey]
        return self._platform_manager.unregister(hotkey)

    def unregister_all(self) -> None:
        """Unregister all hotkeys."""
        for hotkey in list(self._callbacks.keys()):
            self.unregister(hotkey)

    def start(self) -> None:
        """Start listening for hotkey events."""
        self._platform_manager.start()

    def stop(self) -> None:
        """Stop listening for hotkey events."""
        self._platform_manager.stop()

    def is_registered(self, hotkey: str) -> bool:
        """Check if a hotkey is currently registered."""
        return self._platform_manager.is_registered(hotkey)

    def get_registered_hotkeys(self) -> Dict[str, Callable[[], None]]:
        """Get all registered hotkeys and their callbacks."""
        return self._callbacks.copy()

    def update_hotkey(self, old_hotkey: str, new_hotkey: str, callback: Callable[[], None]) -> bool:
        """
        Update a hotkey from one key combination to another.

        Args:
            old_hotkey: The old hotkey to unregister.
            new_hotkey: The new hotkey to register.
            callback: The callback function.

        Returns:
            True if update successful, False otherwise.
        """
        self.unregister(old_hotkey)
        return self.register(new_hotkey, callback)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


def create_hotkey_manager() -> HotkeyManager:
    """Factory function to create a HotkeyManager."""
    return HotkeyManager()