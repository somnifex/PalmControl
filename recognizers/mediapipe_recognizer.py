import cv2
import mediapipe as mp
import time
import queue

class MediapipeRecognizer:
    def __init__(self, input_controller, frame_queue=None):
        self.input_controller = input_controller
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            max_num_hands=1
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Gesture state
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5  # seconds
        
        # Performance optimization
        self.last_process_time = 0
        self.process_interval = 1.0 / 60  # Max 60 FPS processing
        self.frame_skip_count = 0
        self.max_frame_skip = 2
        
        # Hold gesture state
        self.is_holding = False
        self.hold_start_time = 0
        self.hold_threshold = 1.0
        self.last_pinch_state = False
        
        # V-gesture state
        self.v_gesture_frames = 0
        self.v_gesture_threshold = 3
        
        # Quick scroll gesture state
        self.last_hand_y = None
        self.gesture_velocity_threshold = 0.05  # 手势速度阈值
        self.scroll_gesture_frames = 0
        self.scroll_gesture_threshold = 2

    def process_frame(self, frame):
        if self.hands is None:
            return frame
            
        current_time = time.time()
        
        # Frame rate control
        if current_time - self.last_process_time < self.process_interval:
            self.frame_skip_count += 1
            if self.frame_skip_count < self.max_frame_skip:
                return frame
        
        self.frame_skip_count = 0
        self.last_process_time = current_time
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                self._handle_gestures(hand_landmarks)

        return frame

    def _handle_gestures(self, landmarks):
        index_tip = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        thumb_tip = landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        wrist = landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        
        # Mouse movement
        self.input_controller.move_mouse(index_tip.x, index_tip.y)

        # Pinch gesture detection
        pinch_distance = self._calculate_distance(index_tip, thumb_tip)
        is_pinching = pinch_distance < 0.05
        
        current_time = time.time()
        
        # Handle hold gesture
        self._handle_hold_gesture(is_pinching, current_time)
        
        # Handle quick scroll gestures
        self._handle_quick_scroll_gesture(wrist, current_time)
        
        # Handle V-gesture for right-click
        if current_time - self.last_gesture_time > self.gesture_cooldown:
            if self._is_v_sign(landmarks):
                self.v_gesture_frames += 1
                if self.v_gesture_frames >= self.v_gesture_threshold:
                    self.input_controller.right_click()
                    self.last_gesture_time = current_time
                    self.v_gesture_frames = 0
            else:
                self.v_gesture_frames = 0

    def _handle_hold_gesture(self, is_pinching, current_time):
        """Handles the logic for hold gestures."""
        if is_pinching and not self.last_pinch_state:
            # Pinch started
            self.hold_start_time = current_time
            self.last_pinch_state = True
            
        elif is_pinching and self.last_pinch_state:
            # 持续捏合
            hold_duration = current_time - self.hold_start_time
            
            if not self.is_holding and hold_duration >= self.hold_threshold:
                # 开始按住
                self.is_holding = True
                self.input_controller.mouse_down('left')
                print("开始按住")
                
        elif not is_pinching and self.last_pinch_state:
            # 结束捏合
            self.last_pinch_state = False
            
            if self.is_holding:
                # 结束按住
                self.is_holding = False
                self.input_controller.mouse_up('left')
                print("结束按住")
            else:
                # 短时间捏合，执行点击
                hold_duration = current_time - self.hold_start_time
                if hold_duration < self.hold_threshold and current_time - self.last_gesture_time > self.gesture_cooldown:
                    self.input_controller.left_click()
                    self.last_gesture_time = current_time
                    print("执行点击")

    def _handle_quick_scroll_gesture(self, wrist, current_time):
        """处理快速滚动手势"""
        current_y = wrist.y
        
        # 如果这是第一次检测，保存位置
        if self.last_hand_y is None:
            self.last_hand_y = current_y
            return
            
        # 计算垂直移动速度
        y_velocity = current_y - self.last_hand_y
        
        # 检测快速上挥或下挥手势
        if abs(y_velocity) > self.gesture_velocity_threshold and current_time - self.last_gesture_time > self.gesture_cooldown:
            self.scroll_gesture_frames += 1
            
            if self.scroll_gesture_frames >= self.scroll_gesture_threshold:
                if y_velocity < -self.gesture_velocity_threshold:
                    # 快速上挥 - 向上滚动
                    self.input_controller.scroll("up", is_quick=True)
                    print("检测到快速上挥手势 - 向上滚动")
                elif y_velocity > self.gesture_velocity_threshold:
                    # 快速下挥 - 向下滚动
                    self.input_controller.scroll("down", is_quick=True)
                    print("检测到快速下挥手势 - 向下滚动")
                
                self.last_gesture_time = current_time
                self.scroll_gesture_frames = 0
        else:
            # 重置计数器如果没有检测到快速手势
            if abs(y_velocity) <= self.gesture_velocity_threshold:
                self.scroll_gesture_frames = 0
        
        # 更新上一次的位置
        self.last_hand_y = current_y

    def _is_v_sign(self, landmarks):
        """检测V手势（食指和中指伸直，其他手指弯曲）"""
        # 获取关键点
        index_tip = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        index_mcp = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        
        middle_tip = landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        middle_mcp = landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        
        ring_tip = landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        
        pinky_tip = landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        pinky_pip = landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP]
        
        thumb_tip = landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
        
        wrist = landmarks.landmark[self.mp_hands.HandLandmark.WRIST]

        # 检查食指是否伸直（tip比pip高，pip比mcp高）
        index_extended = (index_tip.y < index_pip.y < index_mcp.y)
        
        # 检查中指是否伸直
        middle_extended = (middle_tip.y < middle_pip.y < middle_mcp.y)
        
        # 检查无名指是否弯曲（tip比pip低）
        ring_bent = (ring_tip.y > ring_pip.y)
        
        # 检查小指是否弯曲
        pinky_bent = (pinky_tip.y > pinky_pip.y)
        
        # 检查拇指是否不伸直（避免与食指形成捏合姿势）
        thumb_not_extended = (thumb_tip.y > thumb_ip.y)
        
        # 检查食指和中指之间的距离，确保它们分开
        finger_distance = self._calculate_distance(index_tip, middle_tip)
        fingers_separated = finger_distance > 0.03  # 手指之间有一定距离
        
        # V手势：食指和中指伸直，其他手指弯曲，手指分开
        is_v = (index_extended and middle_extended and 
               ring_bent and pinky_bent and 
               thumb_not_extended and fingers_separated)
        
        return is_v

    def _calculate_distance(self, point1, point2):
        return ((point1.x - point2.x)**2 + (point1.y - point2.y)**2)**0.5

    def set_hold_threshold(self, threshold: float):
        """设置按住阈值（秒）"""
        self.hold_threshold = max(0.5, min(3.0, threshold))
        print(f"Hold threshold set to {self.hold_threshold:.1f} seconds")

    def close(self):
        # 清理按住状态
        if self.is_holding:
            self.input_controller.mouse_up('left')
            self.is_holding = False
            print("关闭时释放按住状态")
        
        # 安全关闭 MediaPipe hands
        if hasattr(self, 'hands') and self.hands is not None:
            try:
                self.hands.close()
            except Exception as e:
                print(f"Warning: Error closing MediaPipe hands: {e}")
            finally:
                self.hands = None

    def get_performance_stats(self):
        """返回性能统计信息"""
        if hasattr(self, 'last_process_time'):
            actual_fps = 1.0 / max(self.process_interval, 0.001)
            return {
                "target_fps": int(actual_fps),
                "frame_skips": getattr(self, 'frame_skip_count', 0)
            }
        return {"target_fps": 60, "frame_skips": 0}
