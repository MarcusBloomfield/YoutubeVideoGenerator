import os
import uuid
import re
import shutil
import ProjectPathManager as paths

def get_transcript_files(folder_path=None):
    """Get all txt files in the transcript folder"""
    folder_path = folder_path or paths.get_transcript_dir()
    transcript_files = []
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for file in os.listdir(folder_path):
            if file.endswith(".txt"):
                # Skip files in the old folder if we're searching in Transcript
                if "old" in file:
                    continue
                transcript_files.append(os.path.join(folder_path, file))
    return transcript_files

def extract_info_from_name(filename):
    """Extract information from the filename"""
    basename = os.path.basename(filename)
    match = re.search(r'(\d+)_([a-f0-9-]+)_(.+)_transcript\.txt', basename)
    if match:
        order_number = match.group(1)
        transcript_id = match.group(2)
        location = match.group(3)
        return order_number, transcript_id, location
    return None, None, None

def process_transcript(file_path, output_dir=None):
    """Process a single transcript file, splitting into sections"""
    output_dir = output_dir or paths.get_audio_dir()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract information from filename
    order_number, transcript_id, location = extract_info_from_name(file_path)
    if not transcript_id:
        print(f"Could not extract transcript ID from filename: {file_path}")
        transcript_id = str(uuid.uuid4())[:8]  # Generate a random ID if not found
        order_number = "000"
        
    print(f"Processing transcript {transcript_id} (Order: {order_number})")
    
    try:
        # Read the transcript file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # For simple transcripts, just copy the whole text to a single output file
        output_filename = f"{order_number}_{transcript_id}_{location}_transcript.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Created transcript file: {output_path}")
        return [output_path]
            
    except Exception as e:
        print(f"Error processing transcript {file_path}: {e}")
        return []

def process_all_transcripts(transcript_dir=None, audio_dir=None):
    """Process all transcript files in the given directory"""
    transcript_dir = transcript_dir or paths.get_transcript_dir() 
    audio_dir = audio_dir or paths.get_audio_dir()
    
    # Ensure directories exist
    os.makedirs(transcript_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    # Get all transcript files
    transcript_files = get_transcript_files(transcript_dir)
    
    output_files = []
    for file_path in transcript_files:
        processed_files = process_transcript(file_path, audio_dir)
        output_files.extend(processed_files)
        
    print(f"Processed {len(transcript_files)} transcript files, creating {len(output_files)} output files")
    return output_files

if __name__ == "__main__":
    process_all_transcripts()
