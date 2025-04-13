import os
import shutil
import sys

def clean_directory(directory_path, preserve_patterns=None):
    """
    Clean a directory by removing all files inside it while preserving the directory itself.
    
    Args:
        directory_path: Path to the directory to clean
        preserve_patterns: List of filename patterns to preserve (e.g., ["video_*"])
        
    Returns:
        tuple: (success, message) - success is a boolean indicating if the operation was successful,
               message contains information about the operation
    """
    try:
        # Check if directory exists
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            return True, f"Directory '{directory_path}' created (was not found)."
        
        # Count files before deletion
        files_count = 0
        preserved_count = 0
        
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                # Check if file should be preserved
                should_preserve = False
                if preserve_patterns:
                    for pattern in preserve_patterns:
                        if filename.startswith(pattern) or filename.endswith(pattern):
                            should_preserve = True
                            preserved_count += 1
                            break
                
                if not should_preserve:
                    files_count += 1
        
        # No files to remove
        if files_count == 0:
            return True, f"Directory '{directory_path}' had no files to clean (preserved {preserved_count} files)."
        
        # Remove files in the directory, preserving specified patterns
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            # Check if file should be preserved
            should_preserve = False
            if preserve_patterns and os.path.isfile(file_path):
                for pattern in preserve_patterns:
                    if filename.startswith(pattern) or filename.endswith(pattern):
                        should_preserve = True
                        break
            
            if not should_preserve:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        
        return True, f"Successfully removed {files_count} files/folders from '{directory_path}' (preserved {preserved_count} files)."
    
    except Exception as e:
        return False, f"Error cleaning directory '{directory_path}': {str(e)}"

def clean_project(preserve_output=True):
    """
    Clean up the project by removing files from specified directories.
    
    Args:
        preserve_output: Whether to preserve files in the Output directory
        
    Returns:
        bool: True if all directories were cleaned successfully, False otherwise
    """
    # Basic directories to always clean
    directories_to_clean = ["Transcript", "Audio", "Scenes"]
    
    print("YouTube Video Generator - Project Cleanup")
    print("=========================================")
    
    success_all = True
    
    # Clean the basic directories
    for directory in directories_to_clean:
        success, message = clean_directory(directory)
        print(f"[{'OK' if success else 'ERROR'}] {message}")
        if not success:
            success_all = False
    
    # Handle Output directory separately if it needs cleaning
    if not preserve_output:
        # Clean Output directory but preserve video files
        success, message = clean_directory("Output", preserve_patterns=["video_"])
        print(f"[{'OK' if success else 'ERROR'}] {message}")
        if not success:
            success_all = False
    else:
        print("[INFO] Output directory preserved to maintain generated videos")
    
    if success_all:
        print("\nProject cleanup completed successfully!")
    else:
        print("\nProject cleanup completed with errors. Check messages above.")
    
    return success_all

if __name__ == "__main__":
    # Default to preserving output files when run directly
    preserve_output = True
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if "--clean-all" in sys.argv:
            preserve_output = False
            print("WARNING: All files including output videos will be deleted!")
    
    clean_project(preserve_output) 