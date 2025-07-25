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
            "max_fps": 120
        }
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.file_path):
            self.save_config(self.defaults)
            return self.defaults
        try:
            with open(self.file_path, 'r') as f:
                user_config = json.load(f)
                # Ensure all keys are present
                config = self.defaults.copy()
                config.update(user_config)
                return config
        except (json.JSONDecodeError, TypeError):
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
