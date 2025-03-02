import cv2
from pose_estimator import PoseEstimator

def start_exercise_session(exercise_type):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Unable to access the camera.")
        return

    print(f"Initiating {exercise_type} session...")

    pose_estimator = PoseEstimator()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Frame capture failed.")
            break

        pose_estimator.analyze_frame(frame, exercise_type)

        cv2.imshow(f'{exercise_type.capitalize()} Session', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    start_exercise_session('squat')  # or 'hammer_curl' 