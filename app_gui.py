import customtkinter as ctk
import tkinter as tk
from tkinter import PhotoImage
import cv2
import numpy as np
from PIL import Image, ImageTk
import queue
import io
import base64

class AppGUI(ctk.CTk):
    def __init__(self, app_logic):
        super().__init__()
        self.app_logic = app_logic
        self.config_manager = app_logic.config_manager
        self.frame_queue = queue.Queue(maxsize=2)
        self.current_photo = None

        self.title("PalmControl Settings")
        self.geometry("600x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.create_widgets()
        self.load_settings()
        self.update_video_feed()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Video display label
        self.video_label = tk.Label(self, text="Camera feed will appear here when active.", bg="#2b2b2b", fg="#ffffff")
        self.video_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_label.grid_remove() # Initially hidden

        # Main control frame
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="ew")
        control_frame.grid_columnconfigure((0, 1), weight=1)

        self.status_label = ctk.CTkLabel(control_frame, text="Status: Stopped", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=(10, 10))

        self.toggle_button = ctk.CTkButton(control_frame, text="Start Control", command=self.app_logic.toggle_control)
        self.toggle_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.show_camera_button = ctk.CTkButton(control_frame, text="Show Camera", command=self.app_logic.toggle_camera_view)
        self.show_camera_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Settings tabs
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.tab_view.add("General")
        self.tab_view.add("Advanced")
        self.tab_view.add("Scroll")

        self.create_general_tab(self.tab_view.tab("General"))
        self.create_advanced_tab(self.tab_view.tab("Advanced"))
        self.create_scroll_tab(self.tab_view.tab("Scroll"))

    def update_video_feed(self):
        try:
            # Process the most recent frame from the queue
            latest_frame = None
            while True:
                try:
                    latest_frame = self.frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            if latest_frame is not None:
                # Validate frame format
                if not isinstance(latest_frame, np.ndarray) or len(latest_frame.shape) != 3 or latest_frame.shape[2] != 3:
                    print(f"Warning: Invalid frame format received.")
                    return
                
                if latest_frame.size == 0:
                    print("Warning: Empty frame received")
                    return
                
                # Ensure correct data type
                if latest_frame.dtype != np.uint8:
                    latest_frame = latest_frame.astype(np.uint8)
                
                try:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2RGB)
                except cv2.error as e:
                    print(f"Warning: OpenCV color conversion failed: {e}")
                    return
                
                # Resize frame for display
                height, width = rgb_frame.shape[:2]
                max_width, max_height = 560, 300
                
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                try:
                    resized_frame = cv2.resize(rgb_frame, (new_width, new_height))
                    pil_image = Image.fromarray(resized_frame)
                    
                    # Convert to PhotoImage for Tkinter
                    img_buffer = io.BytesIO()
                    pil_image.save(img_buffer, format='PNG')
                    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                    
                    photo = tk.PhotoImage(data=img_base64)
                    
                    self.video_label.config(image=photo, text="")
                    self.current_photo = photo
                    
                except Exception as e:
                    print(f"Warning: Image processing failed: {e}")
                    return
                
        except Exception as e:
            print(f"Warning: Error in video feed update: {e}")
            self.video_label.config(image='', text="Video processing active")
        finally:
            self.after(100, self.update_video_feed)

    def toggle_video_visibility(self, show):
        if show:
            self.video_label.grid()
            self.show_camera_button.configure(text="Hide Camera")
        else:
            self.video_label.grid_remove()
            self.show_camera_button.configure(text="Show Camera")
            self.video_label.configure(image='', text="Camera feed hidden.")
            self.current_photo = None

    def create_general_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        self.autostart_switch = ctk.CTkSwitch(tab, text="Start on system startup", command=self.on_autostart_toggle)
        self.autostart_switch.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        self.silent_start_switch = ctk.CTkSwitch(tab, text="Start silently in tray", command=self.on_silent_start_toggle)
        self.silent_start_switch.grid(row=1, column=0, padx=20, pady=15, sticky="w")

        # Mouse Sensitivity
        sensitivity_frame = ctk.CTkFrame(tab, fg_color="transparent")
        sensitivity_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        sensitivity_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(sensitivity_frame, text="Mouse Sensitivity:").grid(row=0, column=0, sticky="w")
        self.sensitivity_slider = ctk.CTkSlider(sensitivity_frame, from_=1, to=4, command=self.on_sensitivity_change)
        self.sensitivity_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.sensitivity_label = ctk.CTkLabel(sensitivity_frame, text="1.5")
        self.sensitivity_label.grid(row=0, column=2, padx=10)

    def create_advanced_tab(self, tab):
        tab.grid_columnconfigure(1, weight=1)

        # Recognizer Model Selection
        ctk.CTkLabel(tab, text="Recognizer Model:").grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.recognizer_menu = ctk.CTkOptionMenu(tab, values=["mediapipe", "gpu"], command=self.on_recognizer_change)
        self.recognizer_menu.grid(row=0, column=1, padx=20, pady=15, sticky="ew")

        # Camera Selection
        ctk.CTkLabel(tab, text="Camera:").grid(row=1, column=0, padx=20, pady=15, sticky="w")
        self.camera_menu = ctk.CTkOptionMenu(tab, values=["0", "1", "2"], command=self.on_camera_change)
        self.camera_menu.grid(row=1, column=1, padx=20, pady=15, sticky="ew")

        # Movement Smoothing
        smoothing_frame = ctk.CTkFrame(tab, fg_color="transparent")
        smoothing_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        smoothing_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(smoothing_frame, text="Movement Smoothing:").grid(row=0, column=0, sticky="w")
        self.smoothing_slider = ctk.CTkSlider(smoothing_frame, from_=0, to=100, command=self.on_smoothing_change)
        self.smoothing_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.smoothing_label = ctk.CTkLabel(smoothing_frame, text="0.3")
        self.smoothing_label.grid(row=0, column=2, padx=10)

        # Max FPS
        fps_frame = ctk.CTkFrame(tab, fg_color="transparent")
        fps_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        fps_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fps_frame, text="Max Movement FPS:").grid(row=0, column=0, sticky="w")
        self.fps_slider = ctk.CTkSlider(fps_frame, from_=30, to=240, command=self.on_fps_change)
        self.fps_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.fps_label = ctk.CTkLabel(fps_frame, text="120")
        self.fps_label.grid(row=0, column=2, padx=10)

        # Hold Threshold
        hold_frame = ctk.CTkFrame(tab, fg_color="transparent")
        hold_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        hold_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hold_frame, text="Hold Threshold (seconds):").grid(row=0, column=0, sticky="w")
        self.hold_slider = ctk.CTkSlider(hold_frame, from_=50, to=300, command=self.on_hold_change)
        self.hold_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.hold_label = ctk.CTkLabel(hold_frame, text="1.0")
        self.hold_label.grid(row=0, column=2, padx=10)

        # Click Stability
        stability_frame = ctk.CTkFrame(tab, fg_color="transparent")
        stability_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        stability_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(stability_frame, text="Click Stability Zone:").grid(row=0, column=0, sticky="w")
        self.stability_slider = ctk.CTkSlider(stability_frame, from_=10, to=50, command=self.on_stability_change)
        self.stability_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.stability_label = ctk.CTkLabel(stability_frame, text="0.02")
        self.stability_label.grid(row=0, column=2, padx=10)

    def create_scroll_tab(self, tab):
        tab.grid_columnconfigure(1, weight=1)

        # Quick Scroll Enable
        quick_scroll_frame = ctk.CTkFrame(tab, fg_color="transparent")
        quick_scroll_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        ctk.CTkLabel(quick_scroll_frame, text="Enable Quick Scroll:").grid(row=0, column=0, sticky="w")
        self.quick_scroll_switch = ctk.CTkSwitch(quick_scroll_frame, text="", command=self.on_quick_scroll_toggle)
        self.quick_scroll_switch.grid(row=0, column=1, padx=20, sticky="e")

        # Quick Scroll Amount
        amount_frame = ctk.CTkFrame(tab, fg_color="transparent")
        amount_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        amount_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(amount_frame, text="Quick Scroll Amount:").grid(row=0, column=0, sticky="w")
        self.scroll_amount_slider = ctk.CTkSlider(amount_frame, from_=50, to=300, command=self.on_scroll_amount_change)
        self.scroll_amount_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.scroll_amount_label = ctk.CTkLabel(amount_frame, text="100")
        self.scroll_amount_label.grid(row=0, column=2, padx=10)

        # Quick Scroll Up Sensitivity
        up_sens_frame = ctk.CTkFrame(tab, fg_color="transparent")
        up_sens_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        up_sens_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(up_sens_frame, text="Up Scroll Sensitivity:").grid(row=0, column=0, sticky="w")
        self.up_sensitivity_slider = ctk.CTkSlider(up_sens_frame, from_=50, to=300, command=self.on_up_sensitivity_change)
        self.up_sensitivity_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.up_sensitivity_label = ctk.CTkLabel(up_sens_frame, text="1.5")
        self.up_sensitivity_label.grid(row=0, column=2, padx=10)

        # Quick Scroll Down Sensitivity
        down_sens_frame = ctk.CTkFrame(tab, fg_color="transparent")
        down_sens_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=15, sticky="ew")
        down_sens_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(down_sens_frame, text="Down Scroll Sensitivity:").grid(row=0, column=0, sticky="w")
        self.down_sensitivity_slider = ctk.CTkSlider(down_sens_frame, from_=50, to=300, command=self.on_down_sensitivity_change)
        self.down_sensitivity_slider.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.down_sensitivity_label = ctk.CTkLabel(down_sens_frame, text="1.5")
        self.down_sensitivity_label.grid(row=0, column=2, padx=10)

        # Information label
        info_label = ctk.CTkLabel(tab, text="快速滚动功能允许您调整上挥和下挥手势的滚动响应。\n启用后，手势识别到快速挥动时会使用这些设置。", 
                                 font=ctk.CTkFont(size=12), text_color="gray60", justify="left", wraplength=500)
        info_label.grid(row=4, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

    def load_settings(self):
        self.autostart_switch.select() if self.config_manager.get("autostart") else self.autostart_switch.deselect()
        self.silent_start_switch.select() if self.config_manager.get("start_silently") else self.silent_start_switch.deselect()
        
        sensitivity = self.config_manager.get("sensitivity")
        self.sensitivity_slider.set(sensitivity)
        self.sensitivity_label.configure(text=f"{sensitivity:.1f}")

        self.recognizer_menu.set(self.config_manager.get("recognizer"))
        self.camera_menu.set(str(self.config_manager.get("camera_id")))
        
        # 加载平滑设置
        smoothing_factor = float(self.config_manager.get("smoothing_factor") or 0.3)
        # 将0.1-1.0转换为0-100的值
        smoothing_value = (smoothing_factor - 0.1) / 0.9 * 100
        self.smoothing_slider.set(smoothing_value)
        self.smoothing_label.configure(text=f"{smoothing_factor:.2f}")
        
        max_fps = int(self.config_manager.get("max_fps") or 120)
        self.fps_slider.set(max_fps)
        self.fps_label.configure(text=str(max_fps))
        
        # 加载按住阈值设置
        hold_threshold = float(self.config_manager.get("hold_threshold") or 1.0)
        # 将0.5-3.0秒转换为50-300的值
        hold_value = (hold_threshold - 0.5) / 2.5 * 250 + 50
        self.hold_slider.set(hold_value)
        self.hold_label.configure(text=f"{hold_threshold:.1f}")

        # 加载点击稳定性设置
        stability_zone = float(self.config_manager.get("click_stability_zone") or 0.02)
        # 将0.01-0.05转换为10-50的值
        stability_value = (stability_zone - 0.01) / 0.04 * 40 + 10
        self.stability_slider.set(stability_value)
        self.stability_label.configure(text=f"{stability_zone:.3f}")

        # 加载快速滚动设置
        quick_scroll_enabled = self.config_manager.get("quick_scroll_enabled")
        if quick_scroll_enabled:
            self.quick_scroll_switch.select()
        else:
            self.quick_scroll_switch.deselect()

        scroll_amount = int(self.config_manager.get("quick_scroll_amount") or 100)
        self.scroll_amount_slider.set(scroll_amount)
        self.scroll_amount_label.configure(text=str(scroll_amount))

        up_sensitivity = float(self.config_manager.get("quick_scroll_up_sensitivity") or 1.5)
        # 将0.5-3.0转换为50-300的值
        up_sens_value = (up_sensitivity - 0.5) / 2.5 * 250 + 50
        self.up_sensitivity_slider.set(up_sens_value)
        self.up_sensitivity_label.configure(text=f"{up_sensitivity:.1f}")

        down_sensitivity = float(self.config_manager.get("quick_scroll_down_sensitivity") or 1.5)
        # 将0.5-3.0转换为50-300的值
        down_sens_value = (down_sensitivity - 0.5) / 2.5 * 250 + 50
        self.down_sensitivity_slider.set(down_sens_value)
        self.down_sensitivity_label.configure(text=f"{down_sensitivity:.1f}")

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

    def on_smoothing_change(self, value):
        # 将0-100的值转换为0.1-1.0
        smoothing = 0.1 + (float(value) / 100) * 0.9
        self.smoothing_label.configure(text=f"{smoothing:.2f}")
        self.config_manager.set("smoothing_factor", smoothing)
        if self.app_logic.input_controller:
            self.app_logic.input_controller.set_smoothing_factor(smoothing)

    def on_fps_change(self, value):
        fps = int(float(value))
        self.fps_label.configure(text=str(fps))
        self.config_manager.set("max_fps", fps)
        if self.app_logic.input_controller:
            self.app_logic.input_controller.set_max_fps(fps)

    def on_hold_change(self, value):
        # 将50-300的值转换为0.5-3.0秒
        hold_threshold = 0.5 + (float(value) - 50) / 250 * 2.5
        self.hold_label.configure(text=f"{hold_threshold:.1f}")
        self.config_manager.set("hold_threshold", hold_threshold)
        if self.app_logic.recognizer and hasattr(self.app_logic.recognizer, 'set_hold_threshold'):
            self.app_logic.recognizer.set_hold_threshold(hold_threshold)

    def on_stability_change(self, value):
        # 将10-50的值转换为0.01-0.05
        stability_zone = 0.01 + (float(value) - 10) / 40 * 0.04
        self.stability_label.configure(text=f"{stability_zone:.3f}")
        self.config_manager.set("click_stability_zone", stability_zone)
        if self.app_logic.input_controller:
            self.app_logic.input_controller.set_click_stability_zone(stability_zone)

    def on_quick_scroll_toggle(self):
        """快速滚动开关回调"""
        is_enabled = self.quick_scroll_switch.get() == 1
        self.config_manager.set("quick_scroll_enabled", is_enabled)
        if self.app_logic.input_controller:
            self.app_logic.input_controller.update_quick_scroll_settings(enabled=is_enabled)

    def on_scroll_amount_change(self, value):
        """滚动量滑块回调"""
        scroll_amount = int(float(value))
        self.scroll_amount_label.configure(text=str(scroll_amount))
        self.config_manager.set("quick_scroll_amount", scroll_amount)
        if self.app_logic.input_controller:
            self.app_logic.input_controller.update_quick_scroll_settings(scroll_amount=scroll_amount)

    def on_up_sensitivity_change(self, value):
        """上挥灵敏度滑块回调"""
        # 将50-300的值转换为0.5-3.0
        sensitivity = 0.5 + (float(value) - 50) / 250 * 2.5
        self.up_sensitivity_label.configure(text=f"{sensitivity:.1f}")
        self.config_manager.set("quick_scroll_up_sensitivity", sensitivity)
        if self.app_logic.input_controller:
            self.app_logic.input_controller.update_quick_scroll_settings(up_sensitivity=sensitivity)

    def on_down_sensitivity_change(self, value):
        """下挥灵敏度滑块回调"""
        # 将50-300的值转换为0.5-3.0
        sensitivity = 0.5 + (float(value) - 50) / 250 * 2.5
        self.down_sensitivity_label.configure(text=f"{sensitivity:.1f}")
        self.config_manager.set("quick_scroll_down_sensitivity", sensitivity)
        if self.app_logic.input_controller:
            self.app_logic.input_controller.update_quick_scroll_settings(down_sensitivity=sensitivity)
