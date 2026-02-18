"""Hotkey management modules."""

from .manager import HotkeyManager, create_hotkey_manager
from .setup_wizard import HotkeySetupWizard, run_setup_wizard

__all__ = [
    'HotkeyManager',
    'create_hotkey_manager',
    'HotkeySetupWizard',
    'run_setup_wizard',
]
