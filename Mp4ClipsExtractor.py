import os
import cv2
import numpy as np
from moviepy import VideoFileClip
import time
import logging
from typing import Tuple, List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Mp4ClipsExtractor:
    def __init__(self, raw_folder="RawVideo", output_folder="Clips", min_clip_duration=2, max_clip_duration=30, scene_threshold=30.0):
        self.raw_folder = raw_folder
        self.output_folder = output_folder
        self.min_clip_duration = min_clip_duration
        self.max_clip_duration = max_clip_duration
        self.scene_threshold = scene_threshold
        
        # Ensure output directory exists
        os.makedirs(self.output_folder, exist_ok=True)
        
        logger.info(f"Mp4ClipsExtractor initialized with: min_dur={min_clip_duration}s, max_dur={max_clip_duration}s, threshold={scene_threshold}")

    def detect_scenes(self, video_path: str) -> Tuple[List[Dict[str, float]], float]:
        """
        Detect scene changes in a video file
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            Tuple containing:
            - List of scene dictionaries (with 'start' and 'end' times)
            - Video frame rate (fps)
        """
        logger.info(f"Detecting scenes in: {video_path}")
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return [], 0.0
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video properties: {fps:.2f} fps, {total_frames} frames, {duration:.2f} seconds")
        
        # Initialize variables
        prev_frame = None
        scenes = []
        current_scene_start = 0
        frame_count = 0
        
        # Process frames to detect scene changes
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert frame to grayscale for comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate frame difference if we have a previous frame
            if prev_frame is not None:
                # Calculate mean absolute difference
                diff = cv2.absdiff(gray, prev_frame)
                score = np.mean(diff)
                
                # If difference exceeds threshold, we found a scene change
                time_since_last_scene = (frame_count - current_scene_start) / fps
                
                if (score > self.scene_threshold and time_since_last_scene >= self.min_clip_duration) or time_since_last_scene >= self.max_clip_duration:
                    # End the current scene
                    scene_end_time = frame_count / fps
                    
                    # Add scene to our list
                    scenes.append({
                        'start': current_scene_start / fps,
                        'end': scene_end_time
                    })
                    logger.debug(f"Scene detected: {current_scene_start/fps:.2f}s - {scene_end_time:.2f}s (diff: {score:.2f})")
                    
                    # Start a new scene
                    current_scene_start = frame_count
            
            # Store current frame as previous
            prev_frame = gray
            frame_count += 1
            
            # Log progress every 500 frames
            if frame_count % 500 == 0:
                logger.info(f"Processed {frame_count}/{total_frames} frames ({frame_count/total_frames*100:.1f}%)")
        
        # Add the final scene if there's one in progress
        if frame_count > current_scene_start:
            scenes.append({
                'start': current_scene_start / fps,
                'end': frame_count / fps
            })
        
        # Release the video capture
        cap.release()
        
        logger.info(f"Scene detection complete: {len(scenes)} scenes found")
        return scenes, fps

    def extract_clips(self, video_file):
        """Extract clips from a video file based on scene changes"""
        video_path = os.path.join(self.raw_folder, video_file)
        logger.info(f"Extracting clips from: {video_path}")
        
        # Detect scenes
        scenes, fps = self.detect_scenes(video_path)
        
        # If no scenes were detected, return empty result
        if not scenes:
            logger.warning(f"No scenes detected in: {video_path}")
            return [], fps
        
        return scenes, fps

    def save_clips(self, video_file, clips, fps):
        """Save the detected clips to output folder"""
        if not clips:
            logger.warning(f"No clips to save for {video_file}")
            return
        
        try:
            # Load the video using moviepy
            video_path = os.path.join(self.raw_folder, video_file)
            
            with VideoFileClip(video_path) as video:
                for i, clip in enumerate(clips):
                    # Format the filename
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    duration = clip['end'] - clip['start']
                    base_name = f"{i+1:03d}_clip_{duration:.1f}sec_{timestamp}"
                    output_file = os.path.join(self.output_folder, f"{base_name}.mp4")
                    
                    # Extract the subclip
                    logger.info(f"Saving clip {i+1}/{len(clips)}: {output_file}")
                    subclip = video.subclipped(clip['start'], clip['end'])
                    
                    # Write the subclip to file
                    subclip.write_videofile(
                        output_file,
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile='temp-audio.m4a',
                        remove_temp=True,
                        preset='medium',
                        fps=fps
                    )
            
        except Exception as e:
            logger.error(f"Error saving clips for {video_file}: {e}")

    def process_videos(self):
        """Process all video files in the raw folder"""
        video_files = [f for f in os.listdir(self.raw_folder) if f.lower().endswith('.mp4')]
        
        if not video_files:
            logger.warning(f"No MP4 files found in {self.raw_folder}")
            return
        
        logger.info(f"Found {len(video_files)} video files to process")
        
        for video_file in video_files:
            clips, fps = self.extract_clips(video_file)
            if clips:
                self.save_clips(video_file, clips, fps)

def main():
    extractor = Mp4ClipsExtractor()
    extractor.process_videos()

if __name__ == "__main__":
    main()
