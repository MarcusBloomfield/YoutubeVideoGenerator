import os
import cv2
import torch
import numpy as np
from torchvision import models, transforms
from PIL import Image
import time
import logging
import re

# Configure logging with more verbose output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensure output goes to console
    ]
)
logger = logging.getLogger(__name__)

class ClipRenamer:
    def __init__(self, clips_folder="Clips"):
        self.clips_folder = clips_folder
        
        logger.info(f"Initializing ClipRenamer with clips folder: {self.clips_folder}")
        
        # Load pre-trained model
        logger.info("Loading pre-trained ResNet model for video analysis...")
        try:
            self.model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
            self.model.eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
        
        # Image transformations for the model
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Initialize categories
        self.categories = None
        
        # Try to load class labels
        try:
            with open('imagenet_classes.txt', 'r') as f:
                categories = [line.strip() for line in f.readlines()]
                
                # Check if the file content is valid (not just an error message)
                if len(categories) > 100:  # Expecting many ImageNet classes
                    self.categories = categories
                    logger.info(f"Loaded {len(self.categories)} categories from imagenet_classes.txt")
                else:
                    logger.warning("ImageNet classes file seems invalid or incomplete")
        except Exception as e:
            logger.warning(f"Could not load ImageNet classes: {e}")

    def analyze_frame(self, frame):
        """Analyze a single frame using the pre-trained model"""
        # Convert frame to PIL Image
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Apply transformations
        input_tensor = self.transform(image).unsqueeze(0)
        
        # Get predictions
        with torch.no_grad():
            output = self.model(input_tensor)
        
        # Get top-5 predictions
        _, indices = torch.topk(output, 5)
        indices = indices.squeeze().tolist()
        
        if isinstance(indices, int):  # Handle case where only one prediction is returned
            indices = [indices]
        
        # Return either category names or generic labels
        if self.categories and len(self.categories) > max(indices):
            return [self.categories[idx] for idx in indices]
        else:
            return [f"object_{idx}" for idx in indices]

    def analyze_video(self, video_path):
        """Analyze a video by sampling frames"""
        logger.info(f"Analyzing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return "unknown_content"
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        logger.info(f"Video has {frame_count} frames, {fps} fps, duration {duration:.2f}s")
        
        # For longer videos, sample more frames
        if duration > 10:
            num_samples = 5
        else:
            num_samples = 3
            
        # Calculate frame positions to sample
        sample_positions = [int(i * frame_count / num_samples) for i in range(num_samples)]
        all_predictions = []
        
        for pos in sample_positions:
            logger.info(f"Analyzing frame at position {pos}")
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if ret:
                try:
                    predictions = self.analyze_frame(frame)
                    logger.info(f"Frame predictions: {predictions}")
                    all_predictions.extend(predictions)
                except Exception as e:
                    logger.error(f"Error analyzing frame: {e}")
            else:
                logger.warning(f"Failed to read frame at position {pos}")
        
        cap.release()
        
        # Handle case where no predictions were made
        if not all_predictions:
            logger.warning("No predictions were made for this video")
            return "unknown_content"
        
        # Count occurrences of each prediction
        prediction_counts = {}
        for pred in all_predictions:
            prediction_counts[pred] = prediction_counts.get(pred, 0) + 1
        
        # Get the top 3 most common predictions
        top_predictions = sorted(prediction_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        logger.info(f"Top predictions: {top_predictions}")
        
        # Create a descriptive name based on the predictions
        descriptive_name = "_".join([pred for pred, _ in top_predictions])
        logger.info(f"Generated descriptive name: {descriptive_name}")
        
        return descriptive_name

    def clean_filename(self, filename):
        """Clean up the filename to be more readable"""
        # Replace underscores with spaces for readability
        name = filename.replace('_', ' ')
        
        # Capitalize each word
        name = ' '.join(word.capitalize() for word in name.split())
        
        # Replace spaces back with underscores for the filename
        return name.replace(' ', '_')

    def rename_clips(self):
        """Rename all clips in the clips folder"""
        logger.info(f"Looking for video clips in {self.clips_folder}")
        
        clip_files = [f for f in os.listdir(self.clips_folder) if f.lower().endswith('.mp4')]
        
        if not clip_files:
            logger.warning(f"No MP4 files found in {self.clips_folder}")
            return
        
        logger.info(f"Found {len(clip_files)} clips to analyze and rename")
        
        for clip_file in clip_files:
            # Original path
            original_path = os.path.join(self.clips_folder, clip_file)
            
            # Extract the sequence number and duration from the filename
            parts = clip_file.split('_')
            if len(parts) >= 3:
                sequence = parts[0]
                
                # Find the duration part (format: XXXsec)
                duration_part = None
                for part in parts:
                    if part.endswith('sec'):
                        duration_part = part
                        break
                        
                if not duration_part:
                    duration_part = "unknown"
            else:
                sequence = "000"
                duration_part = "unknown"
            
            # Analyze the video content
            try:
                content_description = self.analyze_video(original_path)
                
                # Clean up the content description for better readability
                content_description = self.clean_filename(content_description)
                
                # Create new filename
                new_filename = f"{sequence}_{content_description}_{duration_part}.mp4"
                
                # New path
                new_path = os.path.join(self.clips_folder, new_filename)
                
                # Rename the file
                try:
                    os.rename(original_path, new_path)
                    logger.info(f"Renamed: {clip_file} → {new_filename}")
                except Exception as e:
                    logger.error(f"Error renaming {clip_file}: {e}")
            except Exception as e:
                logger.error(f"Error processing clip {clip_file}: {e}")

def main():
    renamer = ClipRenamer()
    renamer.rename_clips()

if __name__ == "__main__":
    try:
        logger.info("Starting ClipRename script")
        main()
        logger.info("ClipRename completed successfully")
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
