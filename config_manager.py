import json
import os

class ConfigManager:
    def __init__(self, file_path='config.json'):
        self.file_path = file_path
        self.defaults = {
            "recognizer": "mediapipe",
            "device": "cpu",
            "camera_id": 0,
            "sensitivity": 2.0,
            "autostart": False,
            "start_silently": True,
            "smoothing_factor": 0.3,
            "max_fps": 120,
            "quick_scroll_enabled": True,
            "quick_scroll_up_sensitivity": 1.5,
            "quick_scroll_down_sensitivity": 1.5,
            "quick_scroll_amount": 100
        }
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.file_path):
            self.save_config(self.defaults)
            return self.defaults
        try:
            with open(self.file_path, 'r') as f:
                user_config = json.load(f)
                # Merge user config with defaults to ensure all keys are present
                config = self.defaults.copy()
                config.update(user_config)
                return config
        except (json.JSONDecodeError, TypeError):
            # If config is corrupted, reset to defaults
            self.save_config(self.defaults)
            return self.defaults

    def save_config(self, config_data):
        self.config = config_data
        with open(self.file_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key):
        return self.config.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save_config(self.config)

    def get_quick_scroll_settings(self):
        """获取快速滚动的所有相关设置"""
        return {
            "enabled": self.get("quick_scroll_enabled"),
            "up_sensitivity": self.get("quick_scroll_up_sensitivity"),
            "down_sensitivity": self.get("quick_scroll_down_sensitivity"),
            "scroll_amount": self.get("quick_scroll_amount")
        }

    def set_quick_scroll_settings(self, enabled=None, up_sensitivity=None, 
                                 down_sensitivity=None, scroll_amount=None):
        """设置快速滚动的相关参数"""
        if enabled is not None:
            self.set("quick_scroll_enabled", enabled)
        if up_sensitivity is not None:
            self.set("quick_scroll_up_sensitivity", up_sensitivity)
        if down_sensitivity is not None:
            self.set("quick_scroll_down_sensitivity", down_sensitivity)
        if scroll_amount is not None:
            self.set("quick_scroll_amount", scroll_amount)

    def is_quick_scroll_enabled(self):
        """检查快速滚动是否启用"""
        return self.get("quick_scroll_enabled")