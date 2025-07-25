import pyautogui
import time
import threading
from collections import deque

class InputController:
    def __init__(self, sensitivity: float = 2.0, config_manager=None):
        self.screen_width, self.screen_height = pyautogui.size()
        self.sensitivity = sensitivity
        self.dead_zone = 0.05
        self.config_manager = config_manager
        
        # Movement smoothing settings
        self.current_x = self.screen_width // 2
        self.current_y = self.screen_height // 2
        self.target_x = self.current_x
        self.target_y = self.current_y
        
        self.smoothing_factor = 0.3  # Lower value for smoother movement (0-1)
        self.position_history = deque(maxlen=5)
        
        # Movement interpolation
        self.is_moving = False
        self.move_thread = None
        self.stop_moving = threading.Event()
        
        # Frame rate control
        self.last_move_time = 0
        self.min_move_interval = 1.0 / 120  # Max 120 FPS
        
        # Click stability settings
        self.click_stability_zone = 0.02
        self.is_clicking = False
        self.click_lock_position = None
        self.click_lock_duration = 0.3
        self.click_lock_start_time = 0
        
        # Position stability detection
        self.stable_position_threshold = 0.015
        self.stable_position_frames = 0
        self.min_stable_frames = 3
        
        # Quick scroll settings
        self.quick_scroll_enabled = True
        self.quick_scroll_up_sensitivity = 1.5
        self.quick_scroll_down_sensitivity = 1.5
        self.quick_scroll_amount = 100
        self.default_scroll_amount = 50
        
        # Load quick scroll settings from config if available
        if self.config_manager:
            self.load_quick_scroll_settings()
        
        print(f"Screen size: {self.screen_width}x{self.screen_height}")
        
        # Optimize pyautogui for performance
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        
        self.enable_performance_mode()

    def move_mouse(self, x: float, y: float):
        """
        Move mouse to normalized coordinates (0.0 to 1.0) with smoothing and stability control.

        Args:
            x (float): Normalized x-coordinate (left to right).
            y (float): Normalized y-coordinate (top to bottom).
        """
        current_time = time.time()
        
        # Frame rate limiting
        if current_time - self.last_move_time < self.min_move_interval:
            return
        
        self.last_move_time = current_time
        
        # Handle click lock
        if self.is_clicking and self.click_lock_position:
            lock_duration = current_time - self.click_lock_start_time
            if lock_duration < self.click_lock_duration:
                dx = abs(x - self.click_lock_position[0])
                dy = abs(y - self.click_lock_position[1])
                if dx < self.click_stability_zone and dy < self.click_stability_zone:
                    return
                else:
                    self.is_clicking = False
                    self.click_lock_position = None
        
        # Apply dead zone
        original_x, original_y = x, y
        if x < self.dead_zone:
            x = self.dead_zone
        elif x > 1 - self.dead_zone:
            x = 1 - self.dead_zone
        
        if y < self.dead_zone:
            y = self.dead_zone
        elif y > 1 - self.dead_zone:
            y = 1 - self.dead_zone

        self._update_position_stability(original_x, original_y)

        # Mirror x-axis for intuitive control
        screen_x = self.screen_width * (1 - x)
        screen_y = self.screen_height * y
        
        # Apply sensitivity scaling
        center_x, center_y = self.screen_width / 2, self.screen_height / 2
        dist_x = screen_x - center_x
        dist_y = screen_y - center_y
        
        raw_x = center_x + dist_x * self.sensitivity
        raw_y = center_y + dist_y * self.sensitivity

        # Clamp to screen boundaries
        raw_x = max(0, min(self.screen_width - 1, raw_x))
        raw_y = max(0, min(self.screen_height - 1, raw_y))
        
        self.position_history.append((raw_x, raw_y))
        
        # Calculate smoothed position
        if len(self.position_history) >= 3:
            smoothed_x, smoothed_y = self._calculate_smoothed_position()
        else:
            smoothed_x, smoothed_y = raw_x, raw_y
        
        self.target_x = smoothed_x
        self.target_y = smoothed_y
        
        self._smooth_move_to_target()
    
    def _calculate_smoothed_position(self):
        """Calculate smoothed position using weighted average."""
        if not self.position_history:
            return self.current_x, self.current_y
        
        # Use exponential moving average
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        
        for i, (x, y) in enumerate(self.position_history):
            weight = (i + 1) ** 1.5
            weighted_x += x * weight
            weighted_y += y * weight
            total_weight += weight
        
        if total_weight > 0:
            return weighted_x / total_weight, weighted_y / total_weight
        else:
            return self.current_x, self.current_y
    
    def _update_position_stability(self, x: float, y: float):
        """Update position stability detection."""
        if hasattr(self, 'last_stable_position'):
            dx = abs(x - self.last_stable_position[0])
            dy = abs(y - self.last_stable_position[1])
            
            if dx < self.stable_position_threshold and dy < self.stable_position_threshold:
                self.stable_position_frames += 1
            else:
                self.stable_position_frames = 0
                self.last_stable_position = (x, y)
        else:
            self.last_stable_position = (x, y)
            self.stable_position_frames = 0
    
    def is_position_stable(self) -> bool:
        """Check if current position is stable enough for click operations."""
        return self.stable_position_frames >= self.min_stable_frames
    
    def _smooth_move_to_target(self):
        """Smoothly interpolate movement to target position."""
        if self.is_clicking:
            smoothing_multiplier = 0.3
        else:
            smoothing_multiplier = 1.0
        
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < 2:
            self.current_x = self.target_x
            self.current_y = self.target_y
            pyautogui.moveTo(int(self.current_x), int(self.current_y))
            return
        
        self.current_x += dx * self.smoothing_factor * smoothing_multiplier
        self.current_y += dy * self.smoothing_factor * smoothing_multiplier
        
        pyautogui.moveTo(int(self.current_x), int(self.current_y))

    def left_click(self):
        """改进的左键点击，带有位置锁定"""
        if not self.is_position_stable():
            print("Action: Left Click (position not stable, ignored)")
            return
            
        print("Action: Left Click")
        # 锁定当前位置
        self._lock_click_position()
        pyautogui.click(button='left')

    def right_click(self):
        """改进的右键点击，带有位置锁定"""
        if not self.is_position_stable():
            print("Action: Right Click (position not stable, ignored)")
            return
            
        print("Action: Right Click")
        # 锁定当前位置
        self._lock_click_position()
        pyautogui.click(button='right')
    
    def mouse_down(self, button='left'):
        """按下鼠标按钮（开始按住），带有位置锁定"""
        if not self.is_position_stable():
            print(f"Action: Mouse Down ({button}) (position not stable, ignored)")
            return
            
        print(f"Action: Mouse Down ({button})")
        # 锁定当前位置
        self._lock_click_position()
        pyautogui.mouseDown(button=button)
    
    def mouse_up(self, button='left'):
        """释放鼠标按钮（结束按住）"""
        print(f"Action: Mouse Up ({button})")
        # 解除位置锁定
        self._unlock_click_position()
        pyautogui.mouseUp(button=button)
    
    def _lock_click_position(self):
        """锁定点击位置，防止抖动"""
        if hasattr(self, 'last_stable_position'):
            self.click_lock_position = self.last_stable_position
            self.is_clicking = True
            self.click_lock_start_time = time.time()
    
    def _unlock_click_position(self):
        """解除点击位置锁定"""
        self.is_clicking = False
        self.click_lock_position = None

    def scroll(self, direction: str, is_quick: bool = False):
        """执行滚动操作
        
        Args:
            direction: "up" 或 "down"
            is_quick: 是否为快速滚动
        """
        if is_quick and self.quick_scroll_enabled:
            # 使用快速滚动设置
            if direction == "up":
                scroll_amount = int(self.quick_scroll_amount * self.quick_scroll_up_sensitivity)
                print(f"Action: Quick Scroll Up (amount: {scroll_amount})")
                pyautogui.scroll(scroll_amount)
            elif direction == "down":
                scroll_amount = int(self.quick_scroll_amount * self.quick_scroll_down_sensitivity)
                print(f"Action: Quick Scroll Down (amount: {scroll_amount})")
                pyautogui.scroll(-scroll_amount)
        else:
            # 使用默认滚动
            print(f"Action: Scroll {direction} (amount: {self.default_scroll_amount})")
            if direction == "up":
                pyautogui.scroll(self.default_scroll_amount)
            elif direction == "down":
                pyautogui.scroll(-self.default_scroll_amount)

    def load_quick_scroll_settings(self):
        """从配置管理器加载快速滚动设置"""
        if self.config_manager:
            settings = self.config_manager.get_quick_scroll_settings()
            self.quick_scroll_enabled = settings["enabled"]
            self.quick_scroll_up_sensitivity = settings["up_sensitivity"]
            self.quick_scroll_down_sensitivity = settings["down_sensitivity"]
            self.quick_scroll_amount = settings["scroll_amount"]
            print(f"Loaded quick scroll settings: enabled={self.quick_scroll_enabled}, "
                  f"up_sens={self.quick_scroll_up_sensitivity}, down_sens={self.quick_scroll_down_sensitivity}, "
                  f"amount={self.quick_scroll_amount}")

    def update_quick_scroll_settings(self, enabled=None, up_sensitivity=None, 
                                   down_sensitivity=None, scroll_amount=None):
        """更新快速滚动设置"""
        if enabled is not None:
            self.quick_scroll_enabled = enabled
        if up_sensitivity is not None:
            self.quick_scroll_up_sensitivity = up_sensitivity
        if down_sensitivity is not None:
            self.quick_scroll_down_sensitivity = down_sensitivity
        if scroll_amount is not None:
            self.quick_scroll_amount = scroll_amount
            
        # 如果有配置管理器，同时更新配置文件
        if self.config_manager:
            self.config_manager.set_quick_scroll_settings(
                enabled=enabled,
                up_sensitivity=up_sensitivity,
                down_sensitivity=down_sensitivity,
                scroll_amount=scroll_amount
            )
        
        print(f"Updated quick scroll settings: enabled={self.quick_scroll_enabled}")

    def get_quick_scroll_info(self):
        """获取当前快速滚动设置信息"""
        return {
            "enabled": self.quick_scroll_enabled,
            "up_sensitivity": self.quick_scroll_up_sensitivity,
            "down_sensitivity": self.quick_scroll_down_sensitivity,
            "scroll_amount": self.quick_scroll_amount,
            "default_scroll_amount": self.default_scroll_amount
        }

    def set_smoothing_factor(self, factor: float):
        """设置平滑因子 (0.1-1.0，值越小越平滑)"""
        self.smoothing_factor = max(0.1, min(1.0, factor))
        
    def set_max_fps(self, fps: int):
        """设置最大移动帧率"""
        self.min_move_interval = 1.0 / max(30, min(240, fps))
        
    def reset_position(self):
        """重置鼠标位置跟踪"""
        self.current_x = self.screen_width // 2
        self.current_y = self.screen_height // 2
        self.target_x = self.current_x
        self.target_y = self.current_y
        self.position_history.clear()
        
        # 重置稳定性状态
        self.stable_position_frames = 0
        if hasattr(self, 'last_stable_position'):
            delattr(self, 'last_stable_position')
        self._unlock_click_position()

    def enable_performance_mode(self):
        """启用高性能模式，优化鼠标移动"""
        try:
            # 在macOS上，可以尝试使用更直接的鼠标移动方法
            import platform
            if platform.system() == "Darwin":  # macOS
                # 尝试禁用鼠标加速等系统干预
                pyautogui.MINIMUM_DURATION = 0
                pyautogui.MINIMUM_SLEEP = 0
        except Exception as e:
            print(f"Warning: Could not enable performance mode: {e}")
    
    def set_click_stability_zone(self, zone_size: float):
        """设置点击稳定区域大小"""
        self.click_stability_zone = max(0.01, min(0.05, zone_size))
    
    def set_stable_frames_threshold(self, frames: int):
        """设置位置稳定所需的最少帧数"""
        self.min_stable_frames = max(1, min(10, frames))
    
    def set_click_lock_duration(self, duration: float):
        """设置点击锁定持续时间"""
        self.click_lock_duration = max(0.1, min(1.0, duration))
    
    def get_stability_info(self):
        """获取当前稳定性信息"""
        return {
            "is_stable": self.is_position_stable(),
            "stable_frames": self.stable_position_frames,
            "min_frames_needed": self.min_stable_frames,
            "is_clicking": self.is_clicking,
            "click_lock_active": self.click_lock_position is not None
        }
