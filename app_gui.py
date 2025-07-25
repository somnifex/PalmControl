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
        self.frame_queue = queue.Queue(maxsize=2) # Queue to hold video frames
        self.current_photo = None  # Store reference to current photo

        self.title("PalmControl Settings")
        self.geometry("600x700") # Increased size for video
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.create_widgets()
        self.load_settings()
        self.update_video_feed() # Start the video update loop

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Allow video label to expand

        # --- Video Display ---
        self.video_label = tk.Label(self, text="Camera feed will appear here when active.", bg="#2b2b2b", fg="#ffffff")
        self.video_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_label.grid_remove() # Hide it initially

        # --- Main Control Frame ---
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="ew")
        control_frame.grid_columnconfigure((0, 1), weight=1)

        self.status_label = ctk.CTkLabel(control_frame, text="Status: Stopped", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=(10, 10))

        self.toggle_button = ctk.CTkButton(control_frame, text="Start Control", command=self.app_logic.toggle_control)
        self.toggle_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.show_camera_button = ctk.CTkButton(control_frame, text="Show Camera", command=self.app_logic.toggle_camera_view)
        self.show_camera_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # --- Settings Tabs ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.tab_view.add("General")
        self.tab_view.add("Advanced")

        self.create_general_tab(self.tab_view.tab("General"))
        self.create_advanced_tab(self.tab_view.tab("Advanced"))

    def update_video_feed(self):
        try:
            # Try to get the latest frame from the queue
            latest_frame = None
            while True:
                try:
                    latest_frame = self.frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Display the latest frame if available
            if latest_frame is not None:
                # Validate frame data type and shape
                if not isinstance(latest_frame, np.ndarray):
                    print(f"Warning: Expected numpy array, got {type(latest_frame)}")
                    return
                
                if len(latest_frame.shape) != 3 or latest_frame.shape[2] != 3:
                    print(f"Warning: Expected 3-channel image, got shape {latest_frame.shape}")
                    return
                
                # Check if frame data is valid
                if latest_frame.size == 0:
                    print("Warning: Empty frame received")
                    return
                
                # Ensure the frame is in the correct data type (uint8)
                if latest_frame.dtype != np.uint8:
                    latest_frame = latest_frame.astype(np.uint8)
                
                try:
                    # Convert OpenCV frame (BGR) to RGB
                    rgb_frame = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2RGB)
                except cv2.error as e:
                    print(f"Warning: OpenCV color conversion failed: {e}")
                    return
                except Exception as e:
                    print(f"Warning: Unexpected error in color conversion: {e}")
                    return
                
                # Resize frame to fit in the video display area
                height, width = rgb_frame.shape[:2]
                max_width, max_height = 560, 300  # Adjust these values as needed
                
                # Calculate scaling factor to maintain aspect ratio
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                try:
                    # Resize the frame
                    resized_frame = cv2.resize(rgb_frame, (new_width, new_height))
                    
                    # Convert to PIL Image
                    pil_image = Image.fromarray(resized_frame)
                    
                    # Convert PIL image to bytes and then to base64
                    import io
                    img_buffer = io.BytesIO()
                    pil_image.save(img_buffer, format='PNG')
                    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                    
                    # Create PhotoImage from base64 data
                    photo = tk.PhotoImage(data=img_base64)
                    
                    # Update the video label and store reference
                    self.video_label.config(image=photo, text="")
                    self.current_photo = photo  # Keep reference to prevent garbage collection
                    
                except Exception as e:
                    print(f"Warning: Image processing failed: {e}")
                    return
                
        except Exception as e:
            print(f"Warning: Error in video feed update: {e}")
            self.video_label.config(image='', text="Video processing active")
        finally:
            self.after(100, self.update_video_feed) # Schedule next update

    def toggle_video_visibility(self, show):
        if show:
            self.video_label.grid()
            self.show_camera_button.configure(text="Hide Camera")
        else:
            self.video_label.grid_remove()
            self.show_camera_button.configure(text="Show Camera")
            # Clear the label when hidden
            self.video_label.configure(image='', text="Camera feed hidden.")
            self.current_photo = None  # Clear photo reference

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
        self.sensitivity_slider = ctk.CTkSlider(sensitivity_frame, from_=1, to=4, command=self.on_sensitivity_change)
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
