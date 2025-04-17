import os
import re
import argparse
from pathlib import Path
from moviepy.editor import VideoFileClip, concatenate_videoclips

def extract_order_number(filename):
    """Extract the ordering number from the start of the filename."""
    match = re.match(r'^(\d+)', os.path.basename(filename))
    if match:
        return int(match.group(1))
    return float('inf')  # Files without numbers go to the end

class MakeYoutubeShort:
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
        
        # YouTube Shorts specs
        self.shorts_width = 1080
        self.shorts_height = 1920
    
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
            output_name = "youtube_short"
        
        # Ensure output name has .mp4 extension
        if not output_name.lower().endswith('.mp4'):
            output_name = f"{output_name}.mp4"
            
        output_file = os.path.join(self.output_folder, output_name)
        
        print(f"Will save YouTube Short as: {output_file}")
        
        # Use moviepy to concatenate the videos
        try:
            # Load all video clips
            clips = [VideoFileClip(mp4) for mp4 in mp4_files]
            
            # Concatenate everything
            combined_clip = concatenate_videoclips(clips)
            
            # Write the result with YouTube Shorts resolution
            combined_clip.write_videofile(
                output_file, 
                codec='libx264', 
                audio_codec='aac',
                preset='medium',
                ffmpeg_params=[
                    # Force 9:16 aspect ratio for YouTube Shorts
                    '-vf', f'scale={self.shorts_width}:{self.shorts_height}:force_original_aspect_ratio=decrease,pad={self.shorts_width}:{self.shorts_height}:(ow-iw)/2:(oh-ih)/2:color=black'
                ]
            )
            
            # Close all clips to free resources
            for clip in clips:
                clip.close()
            combined_clip.close()
            
            print(f"Successfully created YouTube Short: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error creating YouTube Short: {e}")
            import traceback
            traceback.print_exc()
            return None

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Create a YouTube Shorts compatible video from clips in the Scenes folder")
    parser.add_argument("--output", type=str, default="youtube_short", help="Output filename (without .mp4 extension)")
    return parser.parse_args()

def make_youtube_short(output_name=None):
    """Create a YouTube Shorts compatible video from clips in the Scenes folder"""
    shorts_maker = MakeYoutubeShort()
    return shorts_maker.main(output_name)

if __name__ == "__main__":
    args = parse_arguments()
    make_youtube_short(args.output)
