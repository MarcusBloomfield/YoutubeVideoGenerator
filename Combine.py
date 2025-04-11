import os
import re
from pathlib import Path
from moviepy import VideoFileClip, concatenate_videoclips

def extract_order_number(filename):
    """Extract the ordering number from the start of the filename."""
    match = re.match(r'^(\d+)', os.path.basename(filename))
    if match:
        return int(match.group(1))
    return float('inf')  # Files without numbers go to the end

class Combine:
    def __init__(self):
        # Get the current directory
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to the Scenes folder
        self.scenes_folder = os.path.join(self.current_dir, "Scenes")
        
        # Create Output folder if it doesn't exist
        self.output_folder = os.path.join(self.current_dir, "Output")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Created Output folder at {self.output_folder}")
    
    def main(self, output_name=None):
        # Check if Scenes folder exists
        if not os.path.exists(self.scenes_folder):
            print(f"Error: Scenes folder not found at {self.scenes_folder}")
            return
        
        # Get all mp4 files in the Scenes folder
        mp4_files = [os.path.join(self.scenes_folder, f) for f in os.listdir(self.scenes_folder) 
                    if f.lower().endswith('.mp4')]
        
        if not mp4_files:
            print("No MP4 files found in the Scenes folder.")
            return
        
        # Sort the files based on the order number at the start of the filename
        mp4_files.sort(key=extract_order_number)
        
        # Output file path in the Output folder
        if not output_name:
            output_name = "combined_output.mp4"
        elif not output_name.lower().endswith('.mp4'):
            output_name = f"{output_name}.mp4"
            
        output_file = os.path.join(self.output_folder, output_name)
        
        print(f"Will save combined video as: {output_file}")
        
        # Use moviepy to concatenate the videos
        try:
            # Load all video clips
            clips = [VideoFileClip(mp4) for mp4 in mp4_files]
            
            # Concatenate everything
            final_clip = concatenate_videoclips(clips)
            
            # Write the result to a file
            final_clip.write_videofile(output_file)
            
            # Close all clips to free resources
            for clip in clips:
                clip.close()
            final_clip.close()
            
            print(f"Successfully combined videos into {output_file}")
            return output_file
        except Exception as e:
            print(f"Error combining videos: {e}")
            return None

def combine_videos(output_name=None):
    """Legacy function for backwards compatibility"""
    combiner = Combine()
    return combiner.main(output_name)

if __name__ == "__main__":
    combine_videos()
