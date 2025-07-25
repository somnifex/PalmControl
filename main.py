import cv2
import os
import sys
import threading
import queue
from PIL import Image, UnidentifiedImageError
from pystray import Icon as TrayIcon, Menu, MenuItem

from config_manager import ConfigManager
from autostart_manager import AutostartManager
from input_controller import InputController
from recognizers.mediapipe_recognizer import MediapipeRecognizer
from recognizers.gpu_recognizer import GpuRecognizer
from app_gui import AppGUI

class PalmControlApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.autostart_manager = AutostartManager()
        self.input_controller = None
        self.recognizer = None
        self.gui = None
        self.tray_icon = None

        self.is_control_active = False
        self.is_camera_view_visible = False
        self.camera_thread = None
        self.stop_event = threading.Event()

    def run(self):
        # Create GUI first, as it initializes tkinter
        self.gui = AppGUI(self)

        # Setup tray icon (but don't run it yet)
        self.setup_tray_icon()
        
        # Start tray icon in a separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

        # Handle silent start
        if self.config_manager.get("start_silently") and not "--show" in sys.argv:
            self.gui.withdraw() # Hide the window
        
        # Start the main GUI loop
        self.gui.protocol("WM_DELETE_WINDOW", self.on_close_window)
        self.gui.mainloop()

    def setup_tray_icon(self):
        try:
            image = Image.open("icon.png")
        except UnidentifiedImageError:
            print("Warning: icon.png is corrupted or not a valid image. Recreating.")
            os.remove("icon.png")
            image = Image.new('RGB', (32, 32), color = 'blue')
            image.save('icon.png')
        menu = Menu(
            MenuItem('Start Control', self.toggle_control_from_tray, checked=lambda item: self.is_control_active),
            MenuItem('Show Settings', self.show_window),
            Menu.SEPARATOR,
            MenuItem('Exit', self.exit_app)
        )
        self.tray_icon = TrayIcon("PalmControl", image, "PalmControl", menu)

    def load_recognizer(self):
        recognizer_name = self.config_manager.get("recognizer")
        device = self.config_manager.get("device")
        sensitivity = float(self.config_manager.get("sensitivity") or 2.0)
        self.input_controller = InputController(sensitivity=sensitivity)
        
        # 设置平滑参数
        smoothing_factor = float(self.config_manager.get("smoothing_factor") or 0.3)
        max_fps = int(self.config_manager.get("max_fps") or 120)
        self.input_controller.set_smoothing_factor(smoothing_factor)
        self.input_controller.set_max_fps(max_fps)
        
        # 设置点击稳定性参数
        click_stability_zone = float(self.config_manager.get("click_stability_zone") or 0.02)
        self.input_controller.set_click_stability_zone(click_stability_zone)

        if self.recognizer:
            try:
                self.recognizer.close()
            except Exception as e:
                print(f"Warning: Error closing recognizer: {e}")
            finally:
                self.recognizer = None

        if recognizer_name == "gpu":
            self.recognizer = GpuRecognizer(self.input_controller, device=device or "cpu")
        else:
            self.recognizer = MediapipeRecognizer(self.input_controller)
            # 设置按住阈值
            hold_threshold = float(self.config_manager.get("hold_threshold") or 1.0)
            self.recognizer.set_hold_threshold(hold_threshold)
        print(f"INFO: Switched to {recognizer_name} recognizer.")

    def camera_loop(self):
        camera_id = int(self.config_manager.get("camera_id") or 0)
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print("Error: Cannot open camera.")
            if hasattr(self, 'gui') and self.gui is not None:
                self.gui.status_label.configure(text="Error: Camera not found.")
            return

        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Warning: Could not read frame from camera. Skipping.")
                continue
            
            # Make a copy of the original frame for video display
            display_frame = frame.copy()
            
            if self.is_control_active:
                # Process frame for gesture recognition but don't modify display_frame
                self.recognizer.process_frame(frame)

            if self.is_camera_view_visible:
                try:
                    # Only put the original frame in the queue for display
                    self.gui.frame_queue.put_nowait(display_frame)
                except queue.Full:
                    # If the queue is full, just skip this frame
                    pass
            
        cap.release()
        print("INFO: Camera thread stopped.")

    # --- Control Methods ---
    def toggle_control(self):
        self.is_control_active = not self.is_control_active
        if self.is_control_active:
            self.start_control_sequence()
        else:
            self.stop_control_sequence()

    def toggle_control_from_tray(self):
        # This runs in the tray thread, so we schedule the GUI update
        self.gui.after(0, self.toggle_control)

    def start_control_sequence(self):
        self.load_recognizer()
        self.stop_event.clear()
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
        
        # 只有在GUI存在时才更新GUI状态
        if hasattr(self, 'gui') and self.gui is not None:
            self.gui.status_label.configure(text="Status: Running", text_color="#2ECC71")
            self.gui.toggle_button.configure(text="Stop Control")
        
        print("INFO: Control started.")

    def stop_control_sequence(self):
        self.stop_event.set()
        if self.camera_thread:
            self.camera_thread.join(timeout=1)
        if self.recognizer:
            try:
                self.recognizer.close()
            except Exception as e:
                print(f"Warning: Error closing recognizer during stop: {e}")
            finally:
                self.recognizer = None
        
        # 只有在GUI存在时才更新GUI状态
        if hasattr(self, 'gui') and self.gui is not None:
            self.gui.status_label.configure(text="Status: Stopped", text_color="#E74C3C")
            self.gui.toggle_button.configure(text="Start Control")
        
        print("INFO: Control stopped.")

    def toggle_camera_view(self):
        self.is_camera_view_visible = not self.is_camera_view_visible
        self.gui.toggle_video_visibility(self.is_camera_view_visible)

    # --- Settings Methods ---
    def set_autostart(self, enable):
        if enable:
            self.autostart_manager.enable()
        else:
            self.autostart_manager.disable()
        self.config_manager.set("autostart", enable)
        print(f"INFO: Autostart set to {enable}")

    def set_sensitivity(self, value):
        self.config_manager.set("sensitivity", value)
        if self.input_controller:
            self.input_controller.sensitivity = value

    def set_recognizer(self, choice):
        self.config_manager.set("recognizer", choice)
        if self.is_control_active: # Reload if running
            try:
                self.stop_control_sequence()
                self.start_control_sequence()
            except Exception as e:
                print(f"Error switching recognizer: {e}")
                # 确保状态一致
                self.is_control_active = False
                if hasattr(self, 'gui') and self.gui:
                    self.gui.status_label.configure(text="Status: Error", text_color="#E74C3C")
                    self.gui.toggle_button.configure(text="Start Control")

    def set_camera(self, cam_id):
        self.config_manager.set("camera_id", cam_id)
        if self.is_control_active: # Restart to use new camera
            self.stop_control_sequence()
            self.start_control_sequence()

    def set_smoothing_factor(self, value):
        """设置平滑因子"""
        self.config_manager.set("smoothing_factor", value)
        if self.input_controller:
            self.input_controller.set_smoothing_factor(value)

    def set_max_fps(self, value):
        """设置最大FPS"""
        self.config_manager.set("max_fps", value)
        if self.input_controller:
            self.input_controller.set_max_fps(value)

    # --- Window and App Lifecycle ---
    def show_window(self):
        self.gui.after(0, self.gui.deiconify) # Bring window to front

    def on_close_window(self):
        # Instead of closing, hide the window
        self.gui.withdraw()

    def exit_app(self):
        print("INFO: Exiting application...")
        try:
            self.stop_control_sequence()
        except Exception as e:
            print(f"Warning: Error during stop sequence: {e}")
        
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception as e:
            print(f"Warning: Error stopping tray icon: {e}")
        
        try:
            self.gui.quit()
        except Exception as e:
            print(f"Warning: Error quitting GUI: {e}")

if __name__ == "__main__":
    # A simple check for an icon file
    if not os.path.exists("icon.png"):
        print("Warning: icon.png not found. Please create a 32x32 PNG for the tray icon.")
        # Create a placeholder icon
        img = Image.new('RGB', (32, 32), color = 'blue')
        img.save('icon.png')

    app = PalmControlApp()
    app.run()
