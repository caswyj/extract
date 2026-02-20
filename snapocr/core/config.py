"""
Configuration management for SnapOCR.
"""

import json
import os
from pathlib import Path
from typing import Optional, Any, Dict


class Config:
    """Configuration management class with platform-specific storage."""

    DEFAULT_CONFIG: Dict[str, Any] = {
        "hotkey": "ctrl+shift+o",
        "language": "chi_sim+eng",
        "latex_conversion": False,
        "tesseract_path": None,
        "show_notification": True,
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Optional custom config path. If not provided,
                        uses platform-specific default location.
        """
        self._config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._load()

    @staticmethod
    def _get_default_config_path() -> str:
        """Get the platform-specific default config file path."""
        import platform
        system = platform.system().lower()

        if system == 'darwin':
            # macOS: ~/Library/Application Support/SnapOCR/config.json
            config_dir = Path.home() / "Library" / "Application Support" / "SnapOCR"
        elif system == 'windows':
            # Windows: %APPDATA%/SnapOCR/config.json
            config_dir = Path(os.environ.get('APPDATA', '')) / "SnapOCR"
        else:
            # Linux: ~/.config/snapocr/config.json
            config_dir = Path.home() / ".config" / "snapocr"

        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / "config.json")

    def _load(self) -> None:
        """Load configuration from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = value
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
            self._save()

    def _save(self) -> bool:
        """Save configuration to file."""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error: Could not save config file: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key.
            default: Default value if key not found.

        Returns:
            The configuration value.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Set a configuration value.

        Args:
            key: The configuration key.
            value: The value to set.
            save: Whether to save to file immediately.
        """
        self._config[key] = value
        if save:
            self._save()

    def update(self, updates: Dict[str, Any], save: bool = True) -> None:
        """
        Update multiple configuration values.

        Args:
            updates: Dictionary of key-value pairs to update.
            save: Whether to save to file immediately.
        """
        self._config.update(updates)
        if save:
            self._save()

    @property
    def hotkey(self) -> str:
        """Get the configured hotkey."""
        return self._config.get('hotkey', self.DEFAULT_CONFIG['hotkey'])

    @hotkey.setter
    def hotkey(self, value: str) -> None:
        """Set the hotkey."""
        self.set('hotkey', value)

    @property
    def language(self) -> str:
        """Get the OCR language setting."""
        return self._config.get('language', self.DEFAULT_CONFIG['language'])

    @language.setter
    def language(self, value: str) -> None:
        """Set the OCR language."""
        self.set('language', value)

    @property
    def latex_conversion(self) -> bool:
        """Get the LaTeX conversion setting."""
        return self._config.get('latex_conversion', self.DEFAULT_CONFIG['latex_conversion'])

    @latex_conversion.setter
    def latex_conversion(self, value: bool) -> None:
        """Set the LaTeX conversion setting."""
        self.set('latex_conversion', value)

    @property
    def tesseract_path(self) -> Optional[str]:
        """Get the Tesseract executable path."""
        return self._config.get('tesseract_path', self.DEFAULT_CONFIG['tesseract_path'])

    @tesseract_path.setter
    def tesseract_path(self, value: Optional[str]) -> None:
        """Set the Tesseract path."""
        self.set('tesseract_path', value)

    @property
    def config_path(self) -> str:
        """Get the configuration file path."""
        return self._config_path

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save()

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self._config.copy()