import pyautogui

class InputController:
    def __init__(self, sensitivity: float = 2.0):
        self.screen_width, self.screen_height = pyautogui.size()
        self.sensitivity = sensitivity
        self.dead_zone = 0.05
        print(f"Screen size: {self.screen_width}x{self.screen_height}")

    def move_mouse(self, x: float, y: float):
        """
        Moves the mouse to a position specified by normalized coordinates (0.0 to 1.0).

        Args:
            x (float): Normalized x-coordinate (from left to right).
            y (float): Normalized y-coordinate (from top to bottom).
        """
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
        
        final_x = center_x + dist_x * self.sensitivity
        final_y = center_y + dist_y * self.sensitivity

        # Clamp to screen boundaries (should be redundant with dead zone, but good for safety)
        final_x = max(0, min(self.screen_width - 1, final_x))
        final_y = max(0, min(self.screen_height - 1, final_y))

        pyautogui.moveTo(final_x, final_y)

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
