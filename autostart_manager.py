import sys
import os

class AutostartManager:
    def __init__(self):
        self.platform = sys.platform
        self.app_name = "PalmControl"
        # Get the absolute path to the main script
        self.script_path = os.path.abspath("main.py") 

    def is_enabled(self):
        if self.platform == "win32":
            return self._is_enabled_windows()
        elif self.platform == "darwin":
            return self._is_enabled_macos()
        elif self.platform.startswith("linux"):
            return self._is_enabled_linux()
        return False

    def enable(self):
        if self.platform == "win32":
            self._enable_windows()
        elif self.platform == "darwin":
            self._enable_macos()
        elif self.platform.startswith("linux"):
            self._enable_linux()

    def disable(self):
        if self.platform == "win32":
            self._disable_windows()
        elif self.platform == "darwin":
            self._disable_macos()
        elif self.platform.startswith("linux"):
            self._disable_linux()

    # --- Windows Specific --- (using pywin32)
    def _is_enabled_windows(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, self.app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    def _enable_windows(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            # Creates a .bat file to run python script in the background
            bat_path = os.path.join(os.path.dirname(self.script_path), f"{self.app_name}.bat")
            with open(bat_path, "w") as bat_file:
                bat_file.write(f'start "" "{sys.executable}" "{self.script_path}" --silent')
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, bat_path)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error enabling autostart: {e}")

    def _disable_windows(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
            # Remove the .bat file
            bat_path = os.path.join(os.path.dirname(self.script_path), f"{self.app_name}.bat")
            if os.path.exists(bat_path):
                os.remove(bat_path)
        except FileNotFoundError:
            pass # Key or value doesn't exist
        except Exception as e:
            print(f"Error disabling autostart: {e}")

    # --- macOS Specific --- (using launchd)
    def _get_plist_path(self):
        return os.path.expanduser(f"~/Library/LaunchAgents/com.{self.app_name.lower()}.plist")

    def _is_enabled_macos(self):
        return os.path.exists(self._get_plist_path())

    def _enable_macos(self):
        plist_path = self._get_plist_path()
        plist_content = f'''
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>com.{self.app_name.lower()}</string>
            <key>ProgramArguments</key>
            <array>
                <string>{sys.executable}</string>
                <string>{self.script_path}</string>
                <string>--silent</string>
            </array>
            <key>RunAtLoad</key>
            <true/>
        </dict>
        </plist>
        '''
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        os.system(f'launchctl load {plist_path}')

    def _disable_macos(self):
        plist_path = self._get_plist_path()
        if os.path.exists(plist_path):
            os.system(f'launchctl unload {plist_path}')
            os.remove(plist_path)

    # --- Linux Specific --- (using systemd or .desktop file)
    def _get_desktop_file_path(self):
        return os.path.expanduser("~/.config/autostart/PalmControl.desktop")

    def _is_enabled_linux(self):
        return os.path.exists(self._get_desktop_file_path())

    def _enable_linux(self):
        desktop_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(desktop_dir, exist_ok=True)
        desktop_file_path = self._get_desktop_file_path()
        desktop_content = f'''
        [Desktop Entry]
        Type=Application
        Name={self.app_name}
        Exec={sys.executable} {self.script_path} --silent
        Icon=
        Comment=Control your computer with hand gestures.
        X-GNOME-Autostart-enabled=true
        '''
        with open(desktop_file_path, 'w') as f:
            f.write(desktop_content)

    def _disable_linux(self):
        desktop_file_path = self._get_desktop_file_path()
        if os.path.exists(desktop_file_path):
            os.remove(desktop_file_path)
