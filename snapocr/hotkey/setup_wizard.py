"""
Interactive hotkey setup wizard for SnapOCR.
"""

import sys
from typing import Optional

from ..core.config import Config
from .manager import HotkeyManager


class HotkeySetupWizard:
    """Interactive CLI wizard for configuring keyboard shortcuts."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the setup wizard.

        Args:
            config: Optional config instance. Creates new one if not provided.
        """
        self._config = config or Config()

    def run(self) -> str:
        """
        Run the interactive setup wizard.

        Returns:
            The configured hotkey string.
        """
        print("\n" + "=" * 50)
        print("SnapOCR Hotkey Setup Wizard")
        print("=" * 50)
        print()

        # Show current hotkey if exists
        current_hotkey = self._config.hotkey
        print(f"Current hotkey: {current_hotkey}")
        print()

        # Show options
        print("Options:")
        print("  1. Press new hotkey combination")
        print("  2. Enter hotkey manually (e.g., 'ctrl+shift+o')")
        print("  3. Keep current hotkey")
        print("  4. Exit without changes")
        print()

        choice = input("Select option (1-4): ").strip()

        if choice == '1':
            new_hotkey = self._capture_hotkey()
            if new_hotkey:
                self._save_hotkey(new_hotkey)
                return new_hotkey
            else:
                print("Hotkey capture cancelled.")
                return current_hotkey

        elif choice == '2':
            new_hotkey = self._enter_hotkey_manually()
            if new_hotkey:
                self._save_hotkey(new_hotkey)
                return new_hotkey
            else:
                return current_hotkey

        elif choice == '3':
            print(f"Keeping current hotkey: {current_hotkey}")
            return current_hotkey

        elif choice == '4':
            print("No changes made.")
            return current_hotkey

        else:
            print("Invalid choice. No changes made.")
            return current_hotkey

    def _capture_hotkey(self) -> Optional[str]:
        """
        Capture hotkey from keyboard input.

        Returns:
            Captured hotkey string or None if cancelled.
        """
        print("\nPress your desired hotkey combination...")
        print("(Press Escape to cancel)")
        print()

        captured_keys = []

        try:
            from pynput import keyboard

            def on_press(key):
                try:
                    # Check for escape
                    if key == keyboard.Key.esc:
                        print("Cancelled.")
                        return False  # Stop listener

                    # Handle modifier keys
                    if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                        if 'ctrl' not in captured_keys:
                            captured_keys.append('ctrl')
                    elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
                        if 'alt' not in captured_keys:
                            captured_keys.append('alt')
                    elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                        if 'shift' not in captured_keys:
                            captured_keys.append('shift')
                    elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                        # cmd on macOS, win on Windows
                        import platform
                        if platform.system().lower() == 'darwin':
                            if 'cmd' not in captured_keys:
                                captured_keys.append('cmd')
                        else:
                            if 'win' not in captured_keys:
                                captured_keys.append('win')

                    # Handle regular keys
                    elif hasattr(key, 'char') and key.char:
                        captured_keys.append(key.char.lower())
                        return False  # Stop after regular key
                    elif hasattr(key, 'name'):
                        # Special keys like function keys
                        captured_keys.append(key.name.lower())
                        return False

                    # Display current combination
                    print(f"\rCaptured: {'+'.join(captured_keys)}", end='', flush=True)

                except Exception as e:
                    print(f"\nError: {e}")
                    return False

            # Collect events until released
            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()

            if captured_keys:
                hotkey = '+'.join(captured_keys)
                print(f"\n\nCaptured hotkey: {hotkey}")
                return hotkey
            return None

        except ImportError:
            print("Error: pynput is not installed.")
            print("Install with: pip install pynput")
            return None
        except Exception as e:
            print(f"\nError capturing hotkey: {e}")
            return None

    def _enter_hotkey_manually(self) -> Optional[str]:
        """
        Let user enter hotkey string manually.

        Returns:
            Entered hotkey string or None if invalid.
        """
        print("\nEnter hotkey combination.")
        print("Format: modifier+key (e.g., 'ctrl+shift+o', 'cmd+alt+s')")
        print()

        hotkey = input("Hotkey: ").strip().lower()

        # Validate
        if not hotkey:
            print("No hotkey entered.")
            return None

        # Basic validation
        parts = hotkey.split('+')
        if len(parts) < 2:
            print("Warning: Hotkey should include at least one modifier (ctrl, alt, shift, cmd/win).")

        # Normalize
        valid_modifiers = {'ctrl', 'alt', 'shift', 'cmd', 'command', 'win', 'windows', 'super', 'meta', 'option'}
        modifiers = [p for p in parts if p in valid_modifiers]
        key = [p for p in parts if p not in valid_modifiers]

        if not key:
            print("Error: Hotkey must include a non-modifier key.")
            return None

        # Build normalized hotkey
        normalized_parts = modifiers + key
        normalized = '+'.join(normalized_parts)

        print(f"\nNormalized hotkey: {normalized}")
        return normalized

    def _save_hotkey(self, hotkey: str) -> bool:
        """
        Save hotkey to configuration.

        Args:
            hotkey: The hotkey string to save.

        Returns:
            True if saved successfully.
        """
        self._config.hotkey = hotkey
        print(f"\nHotkey saved: {hotkey}")
        print(f"Config file: {self._config.config_path}")
        return True


def run_setup_wizard(config: Optional[Config] = None) -> str:
    """
    Run the hotkey setup wizard.

    Args:
        config: Optional config instance.

    Returns:
        The configured hotkey string.
    """
    wizard = HotkeySetupWizard(config)
    return wizard.run()


if __name__ == '__main__':
    run_setup_wizard()
