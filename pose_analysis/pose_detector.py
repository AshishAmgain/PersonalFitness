import cv2
import mediapipe as mp

class PoseDetector:
    def __init__(self):
        self.pose_model = mp.solutions.pose.Pose()
        self.drawing_utils = mp.solutions.drawing_utils

    def process_frame(self, frame, workout_type):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose_model.process(rgb_frame)

        if results.pose_landmarks:
            self.draw_landmarks(frame, results.pose_landmarks.landmark, workout_type)

        return results

    def draw_landmarks(self, frame, landmarks, workout_type):
        if workout_type == "legs":
            self.draw_leg_lines(frame, landmarks)
        elif workout_type == "arms":
            self.draw_arm_lines(frame, landmarks)

    def draw_arm_lines(self, frame, landmarks):
        # Drawing logic for arm workouts
        right_shoulder = [int(landmarks[11].x * frame.shape[1]), int(landmarks[11].y * frame.shape[0])]
        right_elbow = [int(landmarks[13].x * frame.shape[1]), int(landmarks[13].y * frame.shape[0])]
        right_wrist = [int(landmarks[15].x * frame.shape[1]), int(landmarks[15].y * frame.shape[0])]

        left_shoulder = [int(landmarks[12].x * frame.shape[1]), int(landmarks[12].y * frame.shape[0])]
        left_elbow = [int(landmarks[14].x * frame.shape[1]), int(landmarks[14].y * frame.shape[0])]
        left_wrist = [int(landmarks[16].x * frame.shape[1]), int(landmarks[16].y * frame.shape[0])]

        cv2.line(frame, left_shoulder, left_elbow, (0, 0, 255), 4)
        cv2.line(frame, left_elbow, left_wrist, (0, 0, 255), 4)
        cv2.line(frame, right_shoulder, right_elbow, (0, 0, 255), 4)
        cv2.line(frame, right_elbow, right_wrist, (0, 0, 255), 4)

    def draw_leg_lines(self, frame, landmarks):
        # Drawing logic for leg workouts
        hip = [int(landmarks[23].x * frame.shape[1]), int(landmarks[23].y * frame.shape[0])]
        knee = [int(landmarks[25].x * frame.shape[1]), int(landmarks[25].y * frame.shape[0])]
        shoulder = [int(landmarks[11].x * frame.shape[1]), int(landmarks[11].y * frame.shape[0])]

        cv2.line(frame, shoulder, hip, (178, 102, 255), 2)
        cv2.line(frame, hip, knee, (178, 102, 255), 2)