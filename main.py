import cv2
import sys
import threading
from PIL import Image
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
        # Create GUI
        self.gui = AppGUI(self)

        # Create and run tray icon in a separate thread
        tray_thread = threading.Thread(target=self.setup_tray_icon, daemon=True)
        tray_thread.start()

        # Handle silent start
        if self.config_manager.get("start_silently") and not "--show" in sys.argv:
            self.gui.withdraw() # Hide the window
        
        # Start the main GUI loop
        self.gui.protocol("WM_DELETE_WINDOW", self.on_close_window)
        self.gui.mainloop()

    def setup_tray_icon(self):
        image = Image.open("icon.png") # Make sure you have an icon.png file
        menu = Menu(
            MenuItem('Start Control', self.toggle_control_from_tray, checked=lambda item: self.is_control_active),
            MenuItem('Show Settings', self.show_window),
            Menu.SEPARATOR,
            MenuItem('Exit', self.exit_app)
        )
        self.tray_icon = TrayIcon("PalmControl", image, "PalmControl", menu)
        self.tray_icon.run()

    def load_recognizer(self):
        recognizer_name = self.config_manager.get("recognizer")
        device = self.config_manager.get("device")
        self.input_controller = InputController(sensitivity=self.config_manager.get("sensitivity"))

        if self.recognizer:
            self.recognizer.close()

        if recognizer_name == "gpu":
            self.recognizer = GpuRecognizer(self.input_controller, device=device)
        else:
            self.recognizer = MediapipeRecognizer(self.input_controller)
        print(f"INFO: Switched to {recognizer_name} recognizer.")

    def camera_loop(self):
        cap = cv2.VideoCapture(self.config_manager.get("camera_id"))
        if not cap.isOpened():
            print("Error: Cannot open camera.")
            self.gui.status_label.configure(text="Error: Camera not found.")
            return

        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break
            
            if self.is_control_active:
                frame = self.recognizer.process_frame(frame)

            if self.is_camera_view_visible:
                cv2.imshow('PalmControl View', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'): # Allow closing view with 'q'
                self.toggle_camera_view()

        cap.release()
        cv2.destroyAllWindows()
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
        self.gui.status_label.configure(text="Status: Running", text_color="#2ECC71")
        self.gui.toggle_button.configure(text="Stop Control")
        print("INFO: Control started.")

    def stop_control_sequence(self):
        self.stop_event.set()
        if self.camera_thread:
            self.camera_thread.join(timeout=1)
        if self.recognizer:
            self.recognizer.close()
        self.gui.status_label.configure(text="Status: Stopped", text_color="#E74C3C")
        self.gui.toggle_button.configure(text="Start Control")
        print("INFO: Control stopped.")

    def toggle_camera_view(self):
        self.is_camera_view_visible = not self.is_camera_view_visible
        if not self.is_camera_view_visible:
            cv2.destroyAllWindows()

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
            self.stop_control_sequence()
            self.start_control_sequence()

    def set_camera(self, cam_id):
        self.config_manager.set("camera_id", cam_id)
        if self.is_control_active: # Restart to use new camera
            self.stop_control_sequence()
            self.start_control_sequence()

    # --- Window and App Lifecycle ---
    def show_window(self):
        self.gui.after(0, self.gui.deiconify) # Bring window to front

    def on_close_window(self):
        # Instead of closing, hide the window
        self.gui.withdraw()

    def exit_app(self):
        print("INFO: Exiting application...")
        self.stop_control_sequence()
        if self.tray_icon:
            self.tray_icon.stop()
        self.gui.quit()

if __name__ == "__main__":
    # A simple check for an icon file
    if not os.path.exists("icon.png"):
        print("Warning: icon.png not found. Please create a 32x32 PNG for the tray icon.")
        # Create a placeholder icon
        img = Image.new('RGB', (32, 32), color = 'blue')
        img.save('icon.png')

    app = PalmControlApp()
    app.run()
