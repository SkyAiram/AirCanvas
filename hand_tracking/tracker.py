import cv2
import mediapipe as mp


class HandTracker:
    def __init__(
        self,
        max_hands=1,
        detection_confidence=0.7,
        tracking_confidence=0.7
    ):
        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

        self.mp_draw = mp.solutions.drawing_utils

    def detect(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb_frame)

        landmarks = []

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            h, w, _ = frame.shape

            for landmark in hand.landmark:
                x = int(landmark.x * w)
                y = int(landmark.y * h)

                landmarks.append((x, y))

            self.mp_draw.draw_landmarks(
                frame,
                hand,
                self.mp_hands.HAND_CONNECTIONS
            )

        return frame, landmarks