import cv2
from pose_tracker import PoseTracker

def start_workout_session(exercise_type):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Unable to access the camera.")
        return

    print(f"Starting {exercise_type} workout session...")

    pose_tracker = PoseTracker()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Frame capture failed.")
            break

        pose_tracker.analyze_frame(frame, exercise_type)

        cv2.imshow(f'{exercise_type.capitalize()} Workout', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    start_workout_session('legs')  # or 'arms' 