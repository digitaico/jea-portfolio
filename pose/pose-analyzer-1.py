import cv2
import mediapipe as mp
import argparse

class PoseEstimator:
    def __init__(self):
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Colors for visualization
        self.colors = {
            'joints': (0, 0, 255),      # Red
            'connections': (0, 255, 0),  # Green
            'landmarks': (255, 0, 0),    # Blue
        }
    
    def process_frame(self, frame):
        """Process a single frame and return frame with pose landmarks"""
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process pose
        results = self.pose.process(rgb_frame)
        
        # Draw landmarks if detected
        if results.pose_landmarks:
            # Draw pose landmarks and connections
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=self.colors['landmarks'], 
                    thickness=3, 
                    circle_radius=3
                ),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=self.colors['connections'], 
                    thickness=2
                )
            )
            
            # Highlight key joints
            self._highlight_key_joints(frame, results.pose_landmarks)
        
        return frame, results.pose_landmarks is not None
    
    def _highlight_key_joints(self, frame, landmarks):
        """Highlight important joints with larger circles"""
        height, width = frame.shape[:2]
        
        # Key joints to highlight
        key_joints = [
            (self.mp_pose.PoseLandmark.LEFT_SHOULDER, 'L_SHOULDER'),
            (self.mp_pose.PoseLandmark.RIGHT_SHOULDER, 'R_SHOULDER'),
            (self.mp_pose.PoseLandmark.LEFT_ELBOW, 'L_ELBOW'),
            (self.mp_pose.PoseLandmark.RIGHT_ELBOW, 'R_ELBOW'),
            (self.mp_pose.PoseLandmark.LEFT_WRIST, 'L_WRIST'),
            (self.mp_pose.PoseLandmark.RIGHT_WRIST, 'R_WRIST'),
            (self.mp_pose.PoseLandmark.LEFT_HIP, 'L_HIP'),
            (self.mp_pose.PoseLandmark.RIGHT_HIP, 'R_HIP'),
            (self.mp_pose.PoseLandmark.LEFT_KNEE, 'L_KNEE'),
            (self.mp_pose.PoseLandmark.RIGHT_KNEE, 'R_KNEE'),
            (self.mp_pose.PoseLandmark.LEFT_ANKLE, 'L_ANKLE'),
            (self.mp_pose.PoseLandmark.RIGHT_ANKLE, 'R_ANKLE'),
        ]
        
        for joint_idx, joint_name in key_joints:
            landmark = landmarks.landmark[joint_idx]
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            
            # Draw larger circle for key joints
            cv2.circle(frame, (x, y), 6, self.colors['joints'], -1)
            cv2.circle(frame, (x, y), 8, (255, 255, 255), 2)  # White outline


class VideoProcessor:
    def __init__(self):
        self.pose_estimator = PoseEstimator()
    
    def process_video(self, video_path, output_path='pose_estimation.mp4'):
        """Process video and save with pose landmarks"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Cannot open video {video_path}")
            return False
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Processing video: {width}x{height} @ {fps:.1f} FPS")
        print(f"Total frames: {total_frames}")
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        poses_detected = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            processed_frame, pose_detected = self.pose_estimator.process_frame(frame)
            
            if pose_detected:
                poses_detected += 1
            
            # Add frame counter overlay
            self._add_info_overlay(processed_frame, frame_count, poses_detected, total_frames)
            
            # Write frame
            out.write(processed_frame)
            frame_count += 1
            
            # Progress update
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames})")
        
        # Cleanup
        cap.release()
        out.release()
        
        print(f"\nProcessing complete!")
        print(f"Frames processed: {frame_count}")
        print(f"Poses detected: {poses_detected} ({poses_detected/frame_count*100:.1f}%)")
        print(f"Output saved: {output_path}")
        
        return True
    
    def _add_info_overlay(self, frame, frame_num, poses_detected, total_frames):
        """Add information overlay to frame"""
        height, width = frame.shape[:2]
        
        # Frame counter
        frame_text = f"Frame: {frame_num}/{total_frames}"
        cv2.putText(frame, frame_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Pose detection status
        pose_text = f"Poses detected: {poses_detected}"
        cv2.putText(frame, pose_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Detection rate
        if frame_num > 0:
            detection_rate = (poses_detected / frame_num) * 100
            rate_text = f"Detection rate: {detection_rate:.1f}%"
            cv2.putText(frame, rate_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def process_webcam(self):
        """Process webcam feed in real-time"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Cannot open webcam")
            return False
        
        print("Processing webcam feed. Press 'q' to quit.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            processed_frame, pose_detected = self.pose_estimator.process_frame(frame)
            
            # Add status overlay
            status_text = "Pose: DETECTED" if pose_detected else "Pose: NOT DETECTED"
            color = (0, 255, 0) if pose_detected else (0, 0, 255)
            cv2.putText(processed_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            # Display frame
            cv2.imshow('Pose Estimation', processed_frame)
            
            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return True


def main():
    parser = argparse.ArgumentParser(description='Pose estimation with landmarks overlay')
    parser.add_argument('--video', type=str, help='Path to input video file')
    parser.add_argument('--output', type=str, default='pose_estimation.mp4', help='Output video path')
    parser.add_argument('--webcam', action='store_true', help='Use webcam instead of video file')
    
    args = parser.parse_args()
    
    processor = VideoProcessor()
    
    if args.webcam:
        processor.process_webcam()
    elif args.video:
        processor.process_video(args.video, args.output)
    else:
        print("Please provide either --video path or --webcam flag")
        print("Examples:")
        print("  python pose_estimator.py --video runner.mp4")
        print("  python pose_estimator.py --video runner.mp4 --output my_output.mp4")
        print("  python pose_estimator.py --webcam")


if __name__ == "__main__":
    main()