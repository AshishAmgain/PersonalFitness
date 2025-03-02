import cv2
from pose_detector import PoseDetector

def initiate_workout_session(workout_type):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Unable to access the camera.")
        return

    print(f"Starting {workout_type} workout session...")

    pose_detector = PoseDetector()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Frame capture failed.")
            break

        pose_detector.process_frame(frame, workout_type)

        cv2.imshow(f'{workout_type.capitalize()} Workout', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    initiate_workout_session('legs')  # or 'arms' 