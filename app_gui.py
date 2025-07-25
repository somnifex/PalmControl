import customtkinter as ctk
import cv2

class AppGUI(ctk.CTk):
    def __init__(self, app_logic):
        super().__init__()
        self.app_logic = app_logic
        self.config_manager = app_logic.config_manager

        self.title("PalmControl Settings")
        self.geometry("500x450")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        
        # --- Main Control Frame ---
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        control_frame.grid_columnconfigure((0, 1), weight=1)

        self.status_label = ctk.CTkLabel(control_frame, text="Status: Stopped", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=(10, 10))

        self.toggle_button = ctk.CTkButton(control_frame, text="Start Control", command=self.app_logic.toggle_control)
        self.toggle_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.show_camera_button = ctk.CTkButton(control_frame, text="Show Camera", command=self.app_logic.toggle_camera_view)
        self.show_camera_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # --- Settings Tabs ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.tab_view.add("General")
        self.tab_view.add("Advanced")

        self.create_general_tab(self.tab_view.tab("General"))
        self.create_advanced_tab(self.tab_view.tab("Advanced"))

    def create_general_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        # Autostart
        self.autostart_switch = ctk.CTkSwitch(tab, text="Start on system startup", command=self.on_autostart_toggle)
        self.autostart_switch.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Start Silently
        self.silent_start_switch = ctk.CTkSwitch(tab, text="Start silently in tray", command=self.on_silent_start_toggle)
        self.silent_start_switch.grid(row=1, column=0, padx=20, pady=15, sticky="w")

        # Sensitivity
        sensitivity_frame = ctk.CTkFrame(tab, fg_color="transparent")
        sensitivity_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        sensitivity_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(sensitivity_frame, text="Mouse Sensitivity:").grid(row=0, column=0, sticky="w")
        self.sensitivity_slider = ctk.CTkSlider(sensitivity_frame, from_=0.5, to=3.0, command=self.on_sensitivity_change)
        self.sensitivity_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.sensitivity_label = ctk.CTkLabel(sensitivity_frame, text="1.5")
        self.sensitivity_label.grid(row=0, column=2, padx=10)

    def create_advanced_tab(self, tab):
        tab.grid_columnconfigure(1, weight=1)

        # Recognizer Model
        ctk.CTkLabel(tab, text="Recognizer Model:").grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.recognizer_menu = ctk.CTkOptionMenu(tab, values=["mediapipe", "gpu"], command=self.on_recognizer_change)
        self.recognizer_menu.grid(row=0, column=1, padx=20, pady=15, sticky="ew")

        # Camera Selection
        ctk.CTkLabel(tab, text="Camera:").grid(row=1, column=0, padx=20, pady=15, sticky="w")
        # You can dynamically populate this list if you have multiple cameras
        self.camera_menu = ctk.CTkOptionMenu(tab, values=["0", "1", "2"], command=self.on_camera_change)
        self.camera_menu.grid(row=1, column=1, padx=20, pady=15, sticky="ew")

    def load_settings(self):
        self.autostart_switch.select() if self.config_manager.get("autostart") else self.autostart_switch.deselect()
        self.silent_start_switch.select() if self.config_manager.get("start_silently") else self.silent_start_switch.deselect()
        
        sensitivity = self.config_manager.get("sensitivity")
        self.sensitivity_slider.set(sensitivity)
        self.sensitivity_label.configure(text=f"{sensitivity:.1f}")

        self.recognizer_menu.set(self.config_manager.get("recognizer"))
        self.camera_menu.set(str(self.config_manager.get("camera_id")))

    def on_autostart_toggle(self):
        is_enabled = self.autostart_switch.get() == 1
        self.app_logic.set_autostart(is_enabled)

    def on_silent_start_toggle(self):
        self.config_manager.set("start_silently", self.silent_start_switch.get() == 1)

    def on_sensitivity_change(self, value):
        sensitivity = round(float(value), 1)
        self.sensitivity_label.configure(text=f"{sensitivity:.1f}")
        self.app_logic.set_sensitivity(sensitivity)

    def on_recognizer_change(self, choice):
        self.app_logic.set_recognizer(choice)

    def on_camera_change(self, choice):
        self.app_logic.set_camera(int(choice))
