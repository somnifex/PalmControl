import cv2
import mediapipe as mp
import time
import queue

class MediapipeRecognizer:
    def __init__(self, input_controller, frame_queue=None):
        self.input_controller = input_controller
        # Remove frame_queue parameter as we'll handle it in main.py
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

    def process_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # --- Gesture Recognition Logic ---
                self._handle_gestures(hand_landmarks)

        return frame

    def _handle_gestures(self, landmarks):
        # Landmark coordinates are normalized to [0.0, 1.0]
        index_tip = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        thumb_tip = landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        middle_finger_tip = landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        wrist = landmarks.landmark[self.mp_hands.HandLandmark.WRIST]

        # 1. Mouse Movement (using index finger tip)
        self.input_controller.move_mouse(index_tip.x, index_tip.y)

        # 2. Click Gesture (thumb and index finger pinch)
        pinch_distance = self._calculate_distance(index_tip, thumb_tip)
        
        current_time = time.time()
        if current_time - self.last_gesture_time > self.gesture_cooldown:
            if pinch_distance < 0.05: # Threshold for pinch
                self.input_controller.left_click()
                self.last_gesture_time = current_time
            # 3. Right Click Gesture (V sign - check if middle finger is also up)
            elif self._is_v_sign(landmarks):
                self.input_controller.right_click()
                self.last_gesture_time = current_time

    def _is_v_sign(self, landmarks):
        index_tip = landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        wrist = landmarks.landmark[self.mp_hands.HandLandmark.WRIST]

        # Check if index and middle fingers are up, and others are down
        if index_tip.y < wrist.y and middle_tip.y < wrist.y and ring_tip.y > wrist.y and pinky_tip.y > wrist.y:
            return True
        return False

    def _calculate_distance(self, point1, point2):
        return ((point1.x - point2.x)**2 + (point1.y - point2.y)**2)**0.5

    def close(self):
        self.hands.close()
