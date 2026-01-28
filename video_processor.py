"""
Video Processing Module for Defactra AI
Extracts frames from videos, analyzes them for defects, and generates comprehensive reports
"""

import cv2
import numpy as np
from PIL import Image
import io
import tempfile
import os
from typing import List, Dict, Tuple
import streamlit as st


class VideoProcessor:
    """Process videos for property inspection defect detection"""

    def __init__(self, frame_interval=30, max_frames=100, min_frames=10):
        """
        Initialize video processor

        Args:
            frame_interval: Extract 1 frame every N frames (default: 30 = ~1 frame/sec for 30fps video)
            max_frames: Maximum number of frames to extract
            min_frames: Minimum number of frames to extract
        """
        self.frame_interval = frame_interval
        self.max_frames = max_frames
        self.min_frames = min_frames

    def extract_frames(self, video_path: str, progress_callback=None) -> List[Tuple[Image.Image, float, int]]:
        """
        Extract frames from video at regular intervals

        Args:
            video_path: Path to video file
            progress_callback: Optional callback function for progress updates

        Returns:
            List of tuples (PIL Image, timestamp in seconds, frame number)
        """
        frames = []

        try:
            # Open video
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

            # Calculate frame interval based on video duration
            if total_frames < self.min_frames * self.frame_interval:
                # For short videos, extract more frames
                frame_interval = max(1, total_frames // self.min_frames)
            else:
                frame_interval = self.frame_interval

            # Limit maximum frames
            expected_frames = min(total_frames // frame_interval, self.max_frames)

            frame_count = 0
            extracted_count = 0

            while cap.isOpened() and extracted_count < self.max_frames:
                ret, frame = cap.read()

                if not ret:
                    break

                # Extract frame at intervals
                if frame_count % frame_interval == 0:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame_rgb)

                    # Calculate timestamp
                    timestamp = frame_count / fps if fps > 0 else 0

                    frames.append((pil_image, timestamp, frame_count))
                    extracted_count += 1

                    # Progress callback
                    if progress_callback:
                        progress = extracted_count / expected_frames
                        progress_callback(min(progress, 1.0))

                frame_count += 1

            cap.release()

            return frames

        except Exception as e:
            raise Exception(f"Error extracting frames: {str(e)}")

    def get_video_info(self, video_path: str) -> Dict:
        """
        Get video metadata

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video information
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            info = {
                'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration': 0,
                'format': os.path.splitext(video_path)[1][1:].upper()
            }

            # Calculate duration
            if info['fps'] > 0:
                info['duration'] = info['total_frames'] / info['fps']

            cap.release()

            return info

        except Exception as e:
            raise Exception(f"Error getting video info: {str(e)}")

    def create_video_thumbnail(self, video_path: str, timestamp=0.0) -> Image.Image:
        """
        Create thumbnail from video at specific timestamp

        Args:
            video_path: Path to video file
            timestamp: Time in seconds to extract frame (default: 0)

        Returns:
            PIL Image thumbnail
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)

            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            ret, frame = cap.read()
            cap.release()

            if not ret:
                raise ValueError("Failed to read frame")

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)

            # Create thumbnail
            pil_image.thumbnail((400, 300), Image.Resampling.LANCZOS)

            return pil_image

        except Exception as e:
            raise Exception(f"Error creating thumbnail: {str(e)}")

    def analyze_video_with_ai(self, video_path: str, ai_analyzer, progress_callback=None):
        """
        Analyze entire video using AI defect detection

        Args:
            video_path: Path to video file
            ai_analyzer: Function to analyze images (e.g., analyze_image_with_gemini)
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with analysis results
        """
        # Extract frames
        frames = self.extract_frames(video_path, progress_callback)

        if not frames:
            return {
                'success': False,
                'error': 'No frames could be extracted from video',
                'frames_analyzed': 0
            }

        # Analyze each frame
        all_detections = []
        frame_analyses = []
        non_property_frames = 0

        total_frames = len(frames)

        for idx, (frame_image, timestamp, frame_number) in enumerate(frames):
            if progress_callback:
                progress_callback((idx + 1) / total_frames)

            # Analyze frame
            analysis = ai_analyzer(frame_image)

            # Check if property image
            if not analysis.get('is_property', True):
                non_property_frames += 1
                continue

            # Store frame analysis
            frame_analysis = {
                'frame_number': frame_number,
                'timestamp': timestamp,
                'timestamp_formatted': format_timestamp(timestamp),
                'detections': analysis.get('detections', []),
                'overall_score': analysis.get('overall_condition_score', 0),
                'usability': analysis.get('usability_rating', 'unknown')
            }

            frame_analyses.append(frame_analysis)

            # Add detections with timestamp info
            for detection in analysis.get('detections', []):
                detection_with_time = detection.copy()
                detection_with_time['frame_number'] = frame_number
                detection_with_time['timestamp'] = timestamp
                detection_with_time['timestamp_formatted'] = format_timestamp(timestamp)
                all_detections.append(detection_with_time)

        # Aggregate results
        if not all_detections:
            return {
                'success': True,
                'frames_analyzed': len(frames),
                'non_property_frames': non_property_frames,
                'total_defects': 0,
                'frame_analyses': [],
                'defect_summary': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                'average_score': 100,
                'message': 'No defects detected in video'
            }

        # Calculate summary statistics
        severity_counts = {
            'critical': len([d for d in all_detections if d.get('severity') == 'critical']),
            'high': len([d for d in all_detections if d.get('severity') == 'high']),
            'medium': len([d for d in all_detections if d.get('severity') == 'medium']),
            'low': len([d for d in all_detections if d.get('severity') == 'low'])
        }

        # Calculate average condition score
        scores = [f['overall_score'] for f in frame_analyses if f['overall_score'] > 0]
        average_score = sum(scores) / len(scores) if scores else 0

        # Group similar defects across frames
        defect_timeline = self._create_defect_timeline(all_detections)

        return {
            'success': True,
            'frames_analyzed': len(frames),
            'non_property_frames': non_property_frames,
            'property_frames': len(frame_analyses),
            'total_defects': len(all_detections),
            'unique_defect_types': len(defect_timeline),
            'frame_analyses': frame_analyses,
            'all_detections': all_detections,
            'defect_timeline': defect_timeline,
            'defect_summary': severity_counts,
            'average_score': int(average_score),
            'frames_with_defects': len([f for f in frame_analyses if len(f['detections']) > 0])
        }

    def _create_defect_timeline(self, detections: List[Dict]) -> Dict:
        """
        Group similar defects across frames to create timeline

        Args:
            detections: List of all detections

        Returns:
            Dictionary grouping similar defects by type
        """
        timeline = {}

        for detection in detections:
            defect_type = detection.get('detected_object', 'Unknown')

            # Normalize defect type name
            defect_key = defect_type.lower().strip()

            if defect_key not in timeline:
                timeline[defect_key] = {
                    'defect_type': defect_type,
                    'severity': detection.get('severity', 'medium'),
                    'occurrences': [],
                    'first_seen': detection.get('timestamp', 0),
                    'last_seen': detection.get('timestamp', 0),
                    'frame_count': 0,
                    'avg_confidence': 0
                }

            # Add occurrence
            timeline[defect_key]['occurrences'].append({
                'timestamp': detection.get('timestamp', 0),
                'timestamp_formatted': detection.get('timestamp_formatted', '0:00'),
                'frame_number': detection.get('frame_number', 0),
                'confidence': detection.get('confidence_score', 0),
                'location': detection.get('location', 'Unknown'),
                'description': detection.get('description', '')
            })

            # Update stats
            timeline[defect_key]['last_seen'] = max(
                timeline[defect_key]['last_seen'],
                detection.get('timestamp', 0)
            )
            timeline[defect_key]['frame_count'] += 1

        # Calculate average confidence for each defect type
        for defect_key in timeline:
            occurrences = timeline[defect_key]['occurrences']
            confidences = [o['confidence'] for o in occurrences]
            timeline[defect_key]['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0

        return timeline


def format_timestamp(seconds: float) -> str:
    """
    Format timestamp in seconds to MM:SS format

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string (e.g., "1:23" or "12:45")
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def save_uploaded_video(uploaded_file) -> str:
    """
    Save uploaded video file to temporary location

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Path to saved video file
    """
    # Create temporary file
    suffix = os.path.splitext(uploaded_file.name)[1]
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    # Write uploaded file to temp file
    temp_file.write(uploaded_file.read())
    temp_file.close()

    return temp_file.name


def cleanup_temp_file(file_path: str):
    """
    Clean up temporary file

    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass  # Ignore cleanup errors