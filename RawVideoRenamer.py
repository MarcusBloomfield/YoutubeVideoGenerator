import os
import sys

def rename_video_files(directory="RawVideo", append_string="_processed"):
    """
    Renames all video files in the specified directory by appending a string to their names.
    
    Args:
        directory (str): The directory containing video files to rename
        append_string (str): The string to append to each filename
    """
    # Common video file extensions
    video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm']
    
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' not found.")
        return False
    
    # Counter for renamed files
    renamed_count = 0
    
    try:
        # List all files in the directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
            
            # Check if the file is a video
            _, extension = os.path.splitext(filename)
            if extension.lower() in video_extensions:
                # Create new filename
                name_without_ext = os.path.splitext(filename)[0]
                new_filename = f"{name_without_ext}{append_string}{extension}"
                new_file_path = os.path.join(directory, new_filename)
                
                # Rename the file
                os.rename(file_path, new_file_path)
                print(f"Renamed: {filename} → {new_filename}")
                renamed_count += 1
        
        print(f"\nProcess completed! {renamed_count} video files renamed.")
        return True
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    # Get the string to append from command line arguments if provided
    append_string = "_processed"
    if len(sys.argv) > 1:
        append_string = sys.argv[1]
    
    print(f"Starting video file renaming process with append string: '{append_string}'")
    rename_video_files(append_string=append_string)
