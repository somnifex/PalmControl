import pyautogui
import time
import threading
from collections import deque

class InputController:
    def __init__(self, sensitivity: float = 2.0):
        self.screen_width, self.screen_height = pyautogui.size()
        self.sensitivity = sensitivity
        self.dead_zone = 0.05
        
        # 平滑移动相关设置
        self.current_x = self.screen_width // 2
        self.current_y = self.screen_height // 2
        self.target_x = self.current_x
        self.target_y = self.current_y
        
        # 平滑参数
        self.smoothing_factor = 0.3  # 0-1，值越小越平滑
        self.position_history = deque(maxlen=5)  # 保存最近5个位置用于平滑
        
        # 移动插值相关
        self.is_moving = False
        self.move_thread = None
        self.stop_moving = threading.Event()
        
        # 帧率控制
        self.last_move_time = 0
        self.min_move_interval = 1.0 / 120  # 最大120fps
        
        print(f"Screen size: {self.screen_width}x{self.screen_height}")
        
        # 设置pyautogui参数优化性能
        pyautogui.FAILSAFE = False  # 禁用fail-safe以提高性能
        pyautogui.PAUSE = 0  # 去除默认延迟
        
        # 启用性能模式
        self.enable_performance_mode()

    def move_mouse(self, x: float, y: float):
        """
        Moves the mouse to a position specified by normalized coordinates (0.0 to 1.0).
        Uses smoothing and interpolation for fluid movement.

        Args:
            x (float): Normalized x-coordinate (from left to right).
            y (float): Normalized y-coordinate (from top to bottom).
        """
        current_time = time.time()
        
        # 帧率控制 - 限制移动频率
        if current_time - self.last_move_time < self.min_move_interval:
            return
        
        self.last_move_time = current_time
        
        # Apply dead zone
        if x < self.dead_zone:
            x = self.dead_zone
        elif x > 1 - self.dead_zone:
            x = 1 - self.dead_zone
        
        if y < self.dead_zone:
            y = self.dead_zone
        elif y > 1 - self.dead_zone:
            y = 1 - self.dead_zone

        # Invert x-axis for intuitive mirror-like control
        screen_x = self.screen_width * (1 - x)
        screen_y = self.screen_height * y
        
        # Apply sensitivity
        center_x, center_y = self.screen_width / 2, self.screen_height / 2
        dist_x = screen_x - center_x
        dist_y = screen_y - center_y
        
        raw_x = center_x + dist_x * self.sensitivity
        raw_y = center_y + dist_y * self.sensitivity

        # Clamp to screen boundaries
        raw_x = max(0, min(self.screen_width - 1, raw_x))
        raw_y = max(0, min(self.screen_height - 1, raw_y))
        
        # 添加到位置历史用于平滑
        self.position_history.append((raw_x, raw_y))
        
        # 计算平滑后的位置
        if len(self.position_history) >= 3:
            smoothed_x, smoothed_y = self._calculate_smoothed_position()
        else:
            smoothed_x, smoothed_y = raw_x, raw_y
        
        # 更新目标位置
        self.target_x = smoothed_x
        self.target_y = smoothed_y
        
        # 使用插值移动到目标位置
        self._smooth_move_to_target()
    
    def _calculate_smoothed_position(self):
        """使用加权平均计算平滑位置"""
        if not self.position_history:
            return self.current_x, self.current_y
        
        # 使用指数移动平均
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        
        for i, (x, y) in enumerate(self.position_history):
            # 最新的位置权重更高
            weight = (i + 1) ** 1.5
            weighted_x += x * weight
            weighted_y += y * weight
            total_weight += weight
        
        if total_weight > 0:
            return weighted_x / total_weight, weighted_y / total_weight
        else:
            return self.current_x, self.current_y
    
    def _smooth_move_to_target(self):
        """使用线性插值平滑移动到目标位置"""
        # 计算距离
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        distance = (dx * dx + dy * dy) ** 0.5
        
        # 如果距离很小，直接移动
        if distance < 2:
            self.current_x = self.target_x
            self.current_y = self.target_y
            pyautogui.moveTo(int(self.current_x), int(self.current_y))
            return
        
        # 使用平滑因子进行插值
        self.current_x += dx * self.smoothing_factor
        self.current_y += dy * self.smoothing_factor
        
        # 移动鼠标
        pyautogui.moveTo(int(self.current_x), int(self.current_y))

    def left_click(self):
        print("Action: Left Click")
        pyautogui.click(button='left')

    def right_click(self):
        print("Action: Right Click")
        pyautogui.click(button='right')

    def scroll(self, direction: str):
        print(f"Action: Scroll {direction}")
        scroll_amount = 50  # Adjust as needed
        if direction == "up":
            pyautogui.scroll(scroll_amount)
        elif direction == "down":
            pyautogui.scroll(-scroll_amount)

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
