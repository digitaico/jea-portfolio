import cv2
import mediapipe as mp
import numpy as np
import sys
import argparse

def calculate_stride_length(video_path, runner_height_cm):
    # Initialize MediaPipe Pose with GPU
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,  # Higher complexity for better accuracy
        enable_segmentation=False,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video {video_path}")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video: {width}x{height} @ {fps} FPS")
    print(f"Runner height: {runner_height_cm} cm")
    
    # Setup video writer for output
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('stride_analysis.mp4', fourcc, fps, (width, height))
    
    # Storage for ankle positions and calibration
    left_ankle_positions = []
    right_ankle_positions = []
    frame_count = 0
    pixel_to_cm_ratio = None
    
    # Colors for visualization
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    WHITE = (255, 255, 255)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = pose.process(rgb_frame)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Draw pose landmarks
            mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=BLUE, thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=GREEN, thickness=2)
            )
            
            # Calculate pixel-to-cm ratio using body height (more accurate method)
            if pixel_to_cm_ratio is None:
                # Use shoulder to ankle distance for better calibration
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
                right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
                left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
                right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
                
                # Use average shoulder and ankle positions
                avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
                avg_ankle_y = (left_ankle.y + right_ankle.y) / 2
                
                # Estimate body height as 85% of total height (head to ankle)
                body_height_pixels = abs(avg_shoulder_y - avg_ankle_y) * height
                estimated_shoulder_to_ankle_cm = runner_height_cm * 0.6  # Shoulder to ankle ≈ 60% of height
                
                if body_height_pixels > 0:
                    pixel_to_cm_ratio = estimated_shoulder_to_ankle_cm / body_height_pixels
                    print(f"Calibration: {pixel_to_cm_ratio:.4f} cm/pixel")
            
            # Get ankle positions
            left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
            
            # Convert to pixel coordinates
            left_ankle_px = (int(left_ankle.x * width), int(left_ankle.y * height))
            right_ankle_px = (int(right_ankle.x * width), int(right_ankle.y * height))
            
            # Highlight ankles
            cv2.circle(frame, left_ankle_px, 8, RED, -1)
            cv2.circle(frame, right_ankle_px, 8, RED, -1)
            cv2.putText(frame, 'L', (left_ankle_px[0]-10, left_ankle_px[1]-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, RED, 2)
            cv2.putText(frame, 'R', (right_ankle_px[0]-10, right_ankle_px[1]-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, RED, 2)
            
            # Store positions with frame number
            left_ankle_positions.append((frame_count, left_ankle_px))
            right_ankle_positions.append((frame_count, right_ankle_px))
        
        frame_count += 1
        
        # Write frame to output video
        out.write(frame)
        
        # Display progress
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")
    
    cap.release()
    print(f"Total frames processed: {frame_count}")
    
    # Calculate stride length
    if len(left_ankle_positions) < 10 or len(right_ankle_positions) < 10:
        print("Error: Not enough pose data detected")
        out.release()
        return
    
    if pixel_to_cm_ratio is None:
        print("Error: Could not calibrate pixel-to-cm ratio")
        out.release()
        return
    
    # Find ground contacts (heel strikes) - improved detection
    def find_heel_strikes(ankle_positions, min_gap=15):
        heel_strikes = []
        positions = [pos[1] for pos in ankle_positions]
        
        # Smooth the y-coordinates to reduce noise
        y_coords = [pos[1] for pos in positions]
        smoothed_y = []
        window = 5
        for i in range(len(y_coords)):
            start = max(0, i - window)
            end = min(len(y_coords), i + window + 1)
            smoothed_y.append(np.mean(y_coords[start:end]))
        
        # Find local minima with stricter criteria
        for i in range(min_gap, len(smoothed_y) - min_gap):
            current_y = smoothed_y[i]
            
            # Check if this is a significant local minimum
            is_minimum = True
            min_threshold = 5  # Minimum difference in pixels
            
            for j in range(i - min_gap, i + min_gap):
                if smoothed_y[j] < current_y - min_threshold:
                    is_minimum = False
                    break
            
            # Additional check: ensure it's actually low enough to be ground contact
            if is_minimum and current_y > np.mean(smoothed_y) - np.std(smoothed_y) * 0.5:
                frame_num = ankle_positions[i][0]
                heel_strikes.append((frame_num, positions[i]))
        
        return heel_strikes
    
    # Find heel strikes for both feet
    left_heel_strikes = find_heel_strikes(left_ankle_positions)
    right_heel_strikes = find_heel_strikes(right_ankle_positions)
    
    print(f"Left heel strikes detected: {len(left_heel_strikes)}")
    print(f"Right heel strikes detected: {len(right_heel_strikes)}")
    
    # Calculate stride lengths in cm (only horizontal distance)
    def calculate_strides_cm(heel_strikes):
        strides = []
        for i in range(1, len(heel_strikes)):
            pos1 = heel_strikes[i-1][1]
            pos2 = heel_strikes[i][1]
            
            # Calculate only horizontal distance for stride length
            horizontal_distance_px = abs(pos2[0] - pos1[0])
            distance_cm = horizontal_distance_px * pixel_to_cm_ratio
            
            # Filter out unrealistic strides
            if 50 < distance_cm < 200:  # Reasonable stride range
                strides.append(distance_cm)
        
        return strides
    
    left_strides_cm = calculate_strides_cm(left_heel_strikes)
    right_strides_cm = calculate_strides_cm(right_heel_strikes)
    
    # Calculate current stride for real-time display
    def get_current_stride(frame_num, heel_strikes_left, heel_strikes_right, strides_left, strides_right):
        # Find most recent stride measurement
        recent_stride = None
        
        # Check recent left foot strides
        for i, (strike_frame, _) in enumerate(heel_strikes_left[1:], 1):
            if strike_frame <= frame_num and i-1 < len(strides_left):
                recent_stride = strides_left[i-1]
        
        # Check recent right foot strides
        for i, (strike_frame, _) in enumerate(heel_strikes_right[1:], 1):
            if strike_frame <= frame_num and i-1 < len(strides_right):
                recent_stride = strides_right[i-1]
        
        return recent_stride
    
    # Re-process video with stride overlay
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        
        if results.pose_landmarks:
            # Draw pose landmarks
            mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=BLUE, thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=GREEN, thickness=2)
            )
            
            landmarks = results.pose_landmarks.landmark
            
            # Highlight ankles
            left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
            
            left_ankle_px = (int(left_ankle.x * width), int(left_ankle.y * height))
            right_ankle_px = (int(right_ankle.x * width), int(right_ankle.y * height))
            
            cv2.circle(frame, left_ankle_px, 8, RED, -1)
            cv2.circle(frame, right_ankle_px, 8, RED, -1)
            
            # Get current stride measurement
            current_stride = get_current_stride(frame_count, left_heel_strikes, right_heel_strikes, 
                                              left_strides_cm, right_strides_cm)
            
            # Add stride measurement overlay
            if current_stride:
                stride_text = f"Stride: {current_stride:.1f} cm"
            else:
                avg_stride = np.mean(all_strides) if all_strides else 0
                stride_text = f"Avg Stride: {avg_stride:.1f} cm"
            
            # Create text background
            text_size = cv2.getTextSize(stride_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            cv2.rectangle(frame, (10, 10), (text_size[0] + 20, text_size[1] + 30), (0, 0, 0), -1)
            cv2.putText(frame, stride_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, YELLOW, 3)
            
            # Add additional info
            info_text = f"Height: {runner_height_cm:.0f}cm | Total Strides: {len(all_strides)}"
            cv2.putText(frame, info_text, (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
        
        out.write(frame)
        frame_count += 1
    
    cap.release()
    out.release()
    
    # Display results
    print("\n--- STRIDE ANALYSIS ---")
    
    if left_strides_cm:
        print(f"Left foot strides (cm): {[f'{s:.1f}' for s in left_strides_cm]}")
        print(f"Left foot average stride: {np.mean(left_strides_cm):.1f} cm")
    
    if right_strides_cm:
        print(f"Right foot strides (cm): {[f'{s:.1f}' for s in right_strides_cm]}")
        print(f"Right foot average stride: {np.mean(right_strides_cm):.1f} cm")
    
    if all_strides:
        print(f"Overall average stride: {np.mean(all_strides):.1f} cm")
        print(f"Stride range: {np.min(all_strides):.1f} - {np.max(all_strides):.1f} cm")
    
    print(f"\nOutput video created: stride_analysis.mp4")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze stride length from running video')
    parser.add_argument('--video', type=str, required=True, help='Path to the running video file')
    parser.add_argument('--height-cms', type=float, required=True, help='Runner height in centimeters')
    
    args = parser.parse_args()
    
    print(f"Processing video: {args.video}")
    print(f"Runner height: {args.height_cms} cm")
    
    calculate_stride_length(args.video, args.height_cms)