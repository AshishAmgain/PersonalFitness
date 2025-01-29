from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import cv2
import numpy as np
from pose_estimation.estimation import PoseEstimator
from exercises.squat import Squat
from exercises.hammer_curl import HammerCurl
from exercises.push_up import PushUp
import threading
import os
import math
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variables to control video capture
video_capture = None
is_capturing = False
exercise_thread = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_exercise_score(reps, form_score):
    base_score = reps * 10  # 10 points per rep
    return int(base_score * (form_score / 100))  # Adjust based on form quality

def get_exercise_feedback(exercise_type, angle, form_score):
    feedback = ""
    if exercise_type == "push_up":
        if angle > 160:  # Starting position
            feedback = "Good starting position"
        elif 85 <= angle <= 95:  # Ideal bottom position
            feedback = "Perfect depth!"
        elif angle > 95:
            feedback = "Go lower, aim for 90 degrees"
        elif angle < 85:
            feedback = "You're going too low, maintain form"
    elif exercise_type == "squat":
        if angle > 160:  # Standing position
            feedback = "Good standing position"
        elif 85 <= angle <= 95:  # Ideal squat depth
            feedback = "Perfect squat depth!"
        elif angle > 95:
            feedback = "Squat deeper, keep your back straight"
        elif angle < 85:
            feedback = "You're going too low, maintain form"
    elif exercise_type == "hammer_curl":
        if angle > 160:  # Starting position
            feedback = "Good starting position"
        elif 45 <= angle <= 60:  # Ideal curl position
            feedback = "Perfect curl form!"
        elif angle > 60:
            feedback = "Curl the weight higher"
        elif angle < 45:
            feedback = "Don't swing, maintain control"
    return feedback

def calculate_form_score(exercise_type, angle):
    if exercise_type == "push_up":
        # Ideal angle is 90 degrees at bottom, 180 at top
        if angle > 160:  # Top position
            return 100
        elif 85 <= angle <= 95:  # Perfect bottom position
            return 100
        else:
            return max(0, 100 - abs(90 - angle))
    elif exercise_type == "squat":
        # Ideal angle is 90 degrees at bottom, 180 at top
        if angle > 160:  # Standing straight
            return 100
        elif 85 <= angle <= 95:  # Perfect squat depth
            return 100
        else:
            return max(0, 100 - abs(90 - angle))
    elif exercise_type == "hammer_curl":
        # Ideal angle is 50 degrees at top of curl
        if angle > 160:  # Starting position
            return 100
        elif 45 <= angle <= 60:  # Perfect curl position
            return 100
        else:
            return max(0, 100 - abs(50 - angle) * 2)

def analyze_video(video_path, exercise_type):
    try:
        pose_estimator = PoseEstimator()
        exercise = get_exercise_instance(exercise_type)
        
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        if total_frames == 0:
            raise ValueError("Video file is empty or corrupted")
        
        reps = 0
        form_scores = []
        feedback_list = []
        current_stage = "up"
        prev_angle = None
        
        # Variables for rep detection
        rep_threshold = 20  # Minimum angle change to count as rep
        min_angle_for_rep = {
            "push_up": 85,
            "squat": 85,
            "hammer_curl": 45
        }
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            results = pose_estimator.estimate_pose(frame, exercise_type)
            
            if results.pose_landmarks:
                if exercise_type == "push_up":
                    counter, angle, stage = exercise.track_push_up(results.pose_landmarks.landmark, frame)
                elif exercise_type == "squat":
                    counter, angle, stage = exercise.track_squat(results.pose_landmarks.landmark, frame)
                elif exercise_type == "hammer_curl":
                    counter, angle, _, _, _, _, _, _, stage, _ = exercise.track_hammer_curl(
                        results.pose_landmarks.landmark, frame)
                
                # Calculate form score for this frame
                form_score = calculate_form_score(exercise_type, angle)
                form_scores.append(form_score)
                
                # Get feedback based on form
                feedback = get_exercise_feedback(exercise_type, angle, form_score)
                if feedback:
                    feedback_list.append(feedback)
                
                # Rep counting logic
                if prev_angle is not None:
                    angle_change = abs(angle - prev_angle)
                    if angle_change > rep_threshold:
                        if current_stage == "up" and angle <= min_angle_for_rep[exercise_type]:
                            current_stage = "down"
                        elif current_stage == "down" and angle > 160:
                            current_stage = "up"
                            reps += 1
                
                prev_angle = angle
        
        cap.release()
        
        if frame_count == 0:
            raise ValueError("No frames were processed from the video")
        
        # Calculate metrics
        avg_form_score = sum(form_scores) / len(form_scores) if form_scores else 0
        
        # Get most common feedback excluding "Good" messages
        significant_feedback = [f for f in feedback_list if not f.startswith("Good")]
        common_feedback = max(set(significant_feedback), key=significant_feedback.count) if significant_feedback else "Good form maintained throughout"
        
        # Calculate total score based on reps and form
        base_score = reps * 10  # 10 points per rep
        form_multiplier = avg_form_score / 100
        total_score = int(base_score * form_multiplier)
        
        return {
            'exercise_type': exercise_type,
            'reps_completed': reps,
            'form_score': round(avg_form_score, 1),
            'total_score': total_score,
            'feedback': common_feedback,
            'duration': round(total_frames / fps, 1),
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error analyzing video: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

@app.route('/upload-video', methods=['POST'])
def upload_video():
    try:
        print("Received upload request")
        
        if 'video' not in request.files:
            print("No video file in request")
            return jsonify({'status': 'error', 'error': 'No video file provided'}), 400
        
        file = request.files['video']
        exercise_type = request.form.get('exercise_type')
        
        print(f"Received file: {file.filename}, Exercise type: {exercise_type}")
        
        if not exercise_type:
            return jsonify({'status': 'error', 'error': 'Exercise type not specified'}), 400
        
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'error': f'Invalid file type. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Create uploads directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print(f"Saving file to: {filepath}")
        file.save(filepath)
        print("File saved successfully")
        
        try:
            print("Starting video analysis")
            analysis_results = analyze_video(filepath, exercise_type)
            print("Analysis completed:", analysis_results)
            return jsonify(analysis_results)
        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            return jsonify({'status': 'error', 'error': f'Analysis error: {str(e)}'}), 500
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
                print("Cleaned up uploaded file")
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'status': 'error', 'error': f'Server error: {str(e)}'}), 500

def get_exercise_instance(exercise_type):
    if exercise_type == "hammer_curl":
        return HammerCurl()
    elif exercise_type == "squat":
        return Squat()
    elif exercise_type == "push_up":
        return PushUp()
    else:
        raise ValueError("Invalid exercise type")

def draw_gauge(frame, angle, x, y, radius=50):
    # Draw white circular background with border
    cv2.circle(frame, (x, y), radius + 10, (255, 255, 255), -1)
    cv2.circle(frame, (x, y), radius + 10, (0, 0, 0), 2)
    
    # Draw tick marks with numbers
    for i in range(0, 181, 45):
        angle_rad = math.radians(i - 90)
        start_x = int(x + (radius - 10) * math.cos(angle_rad))
        start_y = int(y + (radius - 10) * math.sin(angle_rad))
        end_x = int(x + radius * math.cos(angle_rad))
        end_y = int(y + radius * math.sin(angle_rad))
        cv2.line(frame, (start_x, start_y), (end_x, end_y), (0, 0, 0), 2)
        
        # Add angle numbers
        if i in [0, 45, 90, 135, 180]:
            text_x = int(x + (radius + 20) * math.cos(angle_rad))
            text_y = int(y + (radius + 20) * math.sin(angle_rad))
            cv2.putText(frame, str(i), (text_x-10, text_y+5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    # Draw the current angle needle
    angle_rad = math.radians(angle - 90)
    end_x = int(x + radius * math.cos(angle_rad))
    end_y = int(y + radius * math.sin(angle_rad))
    cv2.line(frame, (x, y), (end_x, end_y), (0, 0, 255), 3)  # Thicker red needle
    
    # Draw current angle value in the center
    cv2.putText(frame, f"{int(angle)}°", (x-20, y+7),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

def draw_ui_elements(frame, exercise_type, counter, angle, stage, feedback=None):
    # Get frame dimensions
    height, width = frame.shape[:2]
    
    # Create semi-transparent black overlay for UI elements
    # Left side for exercise info and gauge
    overlay = frame.copy()
    cv2.rectangle(overlay, (20, 20), (300, 200), (0, 0, 0), -1)
    # Right side for feedback and tips
    cv2.rectangle(overlay, (width-420, 20), (width-20, 200), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)  # 70% opacity
    
    # Left side elements
    # Draw title with exercise type
    cv2.putText(frame, f"Exercise: {exercise_type.replace('_', ' ').title()}", 
                (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Draw rep counter with background
    cv2.putText(frame, f"Reps: {counter}", (30, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Draw stage indicator with colored background
    stage_color = (0, 0, 255) if stage.lower() == "down" else (0, 255, 0)
    cv2.rectangle(frame, (30, 110), (150, 140), stage_color, -1)
    cv2.putText(frame, f"Stage: {stage}", (35, 130),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Draw progress bar
    progress_width = 250
    progress_height = 15
    progress_x = 30
    progress_y = 160
    
    # Progress bar background
    cv2.rectangle(frame, (progress_x, progress_y), 
                 (progress_x + progress_width, progress_y + progress_height),
                 (100, 100, 100), -1)
    
    # Calculate and draw progress
    progress = min(counter / 12 * progress_width, progress_width)  # 12 reps as target
    if progress > 0:
        cv2.rectangle(frame, (progress_x, progress_y),
                     (progress_x + int(progress), progress_y + progress_height),
                     (0, 255, 0), -1)
    
    # Right side elements
    # Draw angle gauge in top-right
    gauge_x = width - 100
    gauge_y = 100
    draw_gauge(frame, angle, gauge_x, gauge_y, radius=50)
    
    # Draw feedback if available
    if feedback:
        feedback_x = width - 400
        feedback_y = 60
        
        # Different colors for different types of feedback
        feedback_color = (0, 255, 0) if "Good" in feedback else (0, 0, 255)  # Green for good, red for corrections
        
        # Draw feedback with background
        cv2.rectangle(frame, (feedback_x, feedback_y-25), 
                     (feedback_x + 280, feedback_y+5), 
                     feedback_color, -1)
        cv2.putText(frame, feedback, (feedback_x + 10, feedback_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Draw exercise tips
    tips = {
        "push_up": "Keep core tight, elbows at 45°",
        "squat": "Keep chest up, knees aligned",
        "hammer_curl": "Keep arms still, control motion"
    }
    if exercise_type in tips:
        tip_x = width - 400
        tip_y = 120
        # Draw tip with blue background
        cv2.rectangle(frame, (tip_x, tip_y-25), 
                     (tip_x + 280, tip_y+5), 
                     (255, 128, 0), -1)  # Blue background
        cv2.putText(frame, f"Tip: {tips[exercise_type]}", (tip_x + 10, tip_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

def process_video(exercise_type):
    global video_capture, is_capturing
    
    pose_estimator = PoseEstimator()
    exercise = get_exercise_instance(exercise_type)
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Set fixed window size
    window_width = 1280
    window_height = 720
    
    # Set video capture resolution
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, window_width)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, window_height)
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    output_file = os.path.join('output', f'{exercise_type}.avi')
    out = cv2.VideoWriter(output_file, fourcc, 30, (window_width, window_height))
    
    # Create window
    cv2.namedWindow('Exercise', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Exercise', window_width, window_height)
    
    while is_capturing:
        ret, frame = video_capture.read()
        if not ret:
            break
        
        # Flip and process the frame
        frame = cv2.flip(frame, 1)
        
        # Create a slightly larger frame with padding
        padded_frame = np.zeros((window_height, window_width, 3), dtype=np.uint8)
        padded_frame[:] = (255, 255, 255)  # White background
        
        # Calculate scaling to fit the original frame while maintaining aspect ratio
        h, w = frame.shape[:2]
        scale = min(window_width/w, window_height/h) * 0.8
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Resize frame
        frame_resized = cv2.resize(frame, (new_w, new_h))
        
        # Calculate position to center the frame
        y_offset = (window_height - new_h) // 2
        x_offset = (window_width - new_w) // 2
        
        # Place the resized frame in the center of the padded frame
        padded_frame[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame_resized
        
        # Use the padded frame for further processing
        frame = padded_frame
        
        results = pose_estimator.estimate_pose(frame, exercise_type)
        
        if results.pose_landmarks:
            if exercise_type == "push_up":
                counter, angle, stage = exercise.track_push_up(results.pose_landmarks.landmark, frame)
            elif exercise_type == "squat":
                counter, angle, stage = exercise.track_squat(results.pose_landmarks.landmark, frame)
            elif exercise_type == "hammer_curl":
                (counter_right, angle_right, counter_left, angle_left,
                 warning_right, warning_left, progress_right, 
                 progress_left, stage_right, stage_left) = exercise.track_hammer_curl(
                    results.pose_landmarks.landmark, frame)
                counter = counter_right
                angle = angle_right
                stage = stage_right
            
            # Get feedback
            feedback = get_posture_feedback(exercise_type, angle, stage)
            
            # Draw all UI elements in a single function call
            draw_ui_elements(frame, exercise_type, counter, angle, stage, feedback)
        
        # Write frame to output video
        out.write(frame)
        
        # Display frame
        cv2.imshow('Exercise', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    out.release()
    cv2.destroyAllWindows()

def get_posture_feedback(exercise_type, angle, stage):
    feedback = ""
    if exercise_type == "push_up":
        if stage == "down":
            if angle > 100:
                feedback = "Lower your body more"
            elif angle < 70:
                feedback = "You're going too low"
            else:
                feedback = "Good form!"
        else:
            if angle < 160:
                feedback = "Push up fully"
            else:
                feedback = "Good form!"
    elif exercise_type == "squat":
        if stage == "down":
            if angle > 120:
                feedback = "Squat deeper"
            elif angle < 70:
                feedback = "Don't go too low"
            else:
                feedback = "Good depth!"
        else:
            if angle < 160:
                feedback = "Stand up straight"
            else:
                feedback = "Good form!"
    return feedback

@app.route('/start-exercise', methods=['POST'])
def start_exercise():
    global video_capture, is_capturing, exercise_thread
    
    data = request.json
    exercise_type = data.get('exercise')
    
    if not exercise_type:
        return jsonify({'error': 'Exercise type not specified'}), 400
    
    if is_capturing:
        is_capturing = False
        if exercise_thread:
            exercise_thread.join()
    
    video_capture = cv2.VideoCapture(0)
    is_capturing = True
    
    exercise_thread = threading.Thread(target=process_video, args=(exercise_type,))
    exercise_thread.start()
    
    return jsonify({'message': 'Exercise started'})

@app.route('/stop-exercise', methods=['POST'])
def stop_exercise():
    global is_capturing, video_capture, exercise_thread
    
    if is_capturing:
        is_capturing = False
        if exercise_thread:
            exercise_thread.join()
        if video_capture:
            video_capture.release()
    
    return jsonify({'message': 'Exercise stopped'})

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(port=3000)