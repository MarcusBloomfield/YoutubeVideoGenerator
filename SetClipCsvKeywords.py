import os
import cv2
import numpy as np
import logging
import time
import csv
from PIL import Image
import tempfile
from OpenAiQuerying import query_openai, check_api_key
from Prompts import SET_CLIP_CSV_KEYWORDS_PROMPT
from Models import ModelCategories

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
    def __init__(self, clips_folder="Clips", csv_file="clips_data.csv"):
        self.clips_folder = clips_folder
        self.csv_file = csv_file
        
        logger.info(f"Initializing ClipRenamer with clips folder: {self.clips_folder} and CSV file: {self.csv_file}")
        
        # Check if OpenAI API key is available
        self.api_key = check_api_key()
        if not self.api_key:
            logger.error("OpenAI API key not found. Cannot proceed with clip renaming.")
            raise ValueError("OpenAI API key is required")
        
        logger.info("Successfully initialized ClipRenamer with OpenAI capabilities")

    def analyze_frame(self, frame):
        """Analyze a single frame using OpenAI's vision capabilities"""
        # Save frame to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_filename = temp_file.name
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            Image.fromarray(frame_rgb).save(temp_filename)
        
        try:
            # Query OpenAI with the frame
            prompt = "Describe what's happening in this video frame. Return only the description, no other text. No other formatting. Example: A truck driving down a road, on a gloomy day, sorrounded by rocks and trees."
            response = query_openai(
                prompt=prompt,
                model="gpt-4o-mini",
                api_key=self.api_key,
                image_path=temp_filename
            )
            
            logger.info(f"OpenAI analysis: {response}")
            return response
        except Exception as e:
            logger.error(f"Error analyzing frame with OpenAI: {e}")
            return "unknown_content"
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def analyze_video(self, video_path):
        """Analyze a video by sampling frames and using OpenAI to describe content"""
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
        
        # Sample fewer frames to avoid excessive API usage
        num_samples = min(3, max(1, int(duration / 10)))
            
        # Calculate frame positions to sample (beginning, middle, end if possible)
        sample_positions = []
        if num_samples == 1:
            sample_positions = [int(frame_count / 2)]  # Middle frame
        else:
            sample_positions = [int(i * frame_count / (num_samples - 1)) for i in range(num_samples)]
        
        all_descriptions = []
        
        for pos in sample_positions:
            logger.info(f"Analyzing frame at position {pos}")
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if ret:
                try:
                    description = self.analyze_frame(frame)
                    if description and description != "unknown_content":
                        all_descriptions.append(description)
                    # Add a small delay to avoid rate limiting
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error analyzing frame: {e}")
            else:
                logger.warning(f"Failed to read frame at position {pos}")
        
        cap.release()
        
        # Handle case where no descriptions were made
        if not all_descriptions:
            logger.warning("No descriptions were generated for this video")
            return "unknown_content"
        
        # If we have multiple descriptions, ask OpenAI to summarize
        if len(all_descriptions) > 1:
            try:
                summary_prompt = f"Given these descriptions of video frames: {', '.join(all_descriptions)}, provide a single, coherent 2-4 word phrase that best describes the overall video content."
                summary = query_openai(
                    prompt=summary_prompt,
                    model="gpt-4o-mini",
                    api_key=self.api_key
                )
                logger.info(f"Generated summary description: {summary}")
                return summary
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
                # Fall back to the first description if summarization fails
                return all_descriptions[0]
        else:
            return all_descriptions[0]

    def clean_filename(self, filename):
        """Clean up the filename to be more readable and valid"""
        # Remove any invalid filename characters
        name = ''.join(c if c.isalnum() or c in ' _-.,()[]{}' else '_' for c in filename)
        
        # Replace multiple spaces or underscores with a single one
        name = ' '.join(word for word in name.split() if word)
        
        # Capitalize each word
        name = ' '.join(word.capitalize() for word in name.split())
        
        name = name.replace('_unknown', '')

        # Replace spaces with underscores for the filename
        return name.replace(' ', '')

    def read_csv_data(self):
        """Read the CSV file and return the data as a dictionary with filelocation as key"""
        if not os.path.exists(self.csv_file):
            logger.warning(f"CSV file not found: {self.csv_file}")
            return {}
        
        csv_data = {}
        try:
            with open(self.csv_file, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Use the filelocation as the key (clip path)
                    csv_data[row['filelocation']] = row
            
            logger.info(f"Successfully read {len(csv_data)} entries from CSV file")
            return csv_data
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return {}
    
    def write_csv_data(self, csv_data):
        """Write the updated CSV data back to the file"""
        try:
            # Get the fieldnames from the first entry or use default ones
            if csv_data:
                first_key = next(iter(csv_data))
                fieldnames = csv_data[first_key].keys()
            else:
                fieldnames = ["id", "date", "location", "length", "filelocation", "keywords"]
            
            # Write to the CSV file
            with open(self.csv_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in csv_data.values():
                    writer.writerow(row)
            
            logger.info(f"Successfully wrote {len(csv_data)} entries to CSV file")
            return True
        except Exception as e:
            logger.error(f"Error writing CSV file: {e}")
            return False

    def update_single_entry(self, csv_data, entry_key, updated_entry):
        """Update a single entry in the CSV file without rewriting the entire file"""
        try:
            # Get the fieldnames from the first entry or use default ones
            if csv_data:
                first_key = next(iter(csv_data))
                fieldnames = csv_data[first_key].keys()
            else:
                fieldnames = ["id", "date", "location", "length", "filelocation", "keywords"]
            
            # Create a temporary file
            temp_file = self.csv_file + '.temp'
            
            # Write all data including the updated entry to the temp file
            with open(temp_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for key, row in csv_data.items():
                    if key == entry_key:
                        writer.writerow(updated_entry)
                    else:
                        writer.writerow(row)
            
            # Replace the original file with the temp file
            os.replace(temp_file, self.csv_file)
            
            logger.info(f"Successfully updated entry in CSV file")
            return True
        except Exception as e:
            logger.error(f"Error updating entry in CSV file: {e}")
            return False

    def rename_clips(self):
        """Update CSV file with keywords for clips that don't have them yet"""
        logger.info(f"Looking for video clips in {self.clips_folder}")
        
        # Ensure clips folder exists
        if not os.path.exists(self.clips_folder):
            logger.warning(f"Clips folder not found: {self.clips_folder}")
            return
            
        # Read the CSV data
        csv_data = self.read_csv_data()
        if csv_data is None:
            logger.error("Failed to read CSV data")
            return
        
        # Get all MP4 files in the clips folder
        clip_files = [f for f in os.listdir(self.clips_folder) if f.lower().endswith('.mp4')]
        
        if not clip_files:
            logger.warning(f"No MP4 files found in {self.clips_folder}")
            return
        
        logger.info(f"Found {len(clip_files)} clips to check for keywords")
        
        for clip_file in clip_files:
            # Full path to the clip
            clip_path = os.path.join(self.clips_folder, clip_file)
            
            # Check if this clip is in the CSV
            csv_entry = None
            entry_key = None
            for file_path, entry in csv_data.items():
                # Normalize paths for comparison
                norm_file_path = file_path.replace('/', '\\')
                norm_clip_path = clip_path.replace('/', '\\')
                
                if norm_file_path.lower() == norm_clip_path.lower():
                    csv_entry = entry
                    entry_key = file_path
                    break
            
            # If clip not found in CSV, log and continue
            if csv_entry is None:
                logger.warning(f"Clip not found in CSV: {clip_path}")
                continue
            
            # Check if the clip already has keywords
            if not csv_entry.get('keywords'):
                logger.info(f"Generating keywords for clip: {clip_file}")
                
                try:
                    # Analyze the video content
                    content_description = self.analyze_video(clip_path)
                    
                    # Clean up the content description for better readability
                    content_description = self.clean_filename(content_description)
                    
                    # Update the CSV entry with keywords
                    csv_entry['keywords'] = content_description
                    
                    # Write this single update to the CSV file immediately
                    if self.update_single_entry(csv_data, entry_key, csv_entry):
                        logger.info(f"Immediately wrote keywords for {clip_file}: {content_description}")
                    else:
                        logger.error(f"Failed to write keywords for {clip_file}")
                        
                    # Update the in-memory CSV data for future operations
                    csv_data[entry_key] = csv_entry
                except Exception as e:
                    logger.error(f"Error generating keywords for {clip_file}: {e}")
        
        logger.info("All clips have been processed individually")

def process_clip_csv(csv_path, output_path=None):
    """
    Process a CSV file containing clip information and generate keywords
    
    Args:
        csv_path: Path to the input CSV file
        output_path: Path to save the output CSV file (optional)
        
    Returns:
        Path to the output CSV file
    """
    try:
        # Read the CSV file
        clips = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                clips.append(row)
        
        # Process each clip
        for clip in clips:
            # Create prompt for keyword generation
            prompt = SET_CLIP_CSV_KEYWORDS_PROMPT.format(
                title=clip['title'],
                description=clip['description']
            )
            
            # Query OpenAI to generate keywords
            response = query_openai(prompt, model=ModelCategories.getDefaultModel())
            
            if response:
                # Update the clip with generated keywords
                clip['keywords'] = response.strip()
                print(f"Generated keywords for: {clip['title']}")
            else:
                print(f"Error generating keywords for: {clip['title']}")
                clip['keywords'] = ""
        
        # Determine output path
        if not output_path:
            base_name = os.path.splitext(csv_path)[0]
            output_path = f"{base_name}_with_keywords.csv"
        
        # Write the updated CSV file
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=clips[0].keys())
            writer.writeheader()
            writer.writerows(clips)
            
        print(f"Updated CSV saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return None

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
