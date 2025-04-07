import os
import uuid
import re
import shutil

def get_transcript_files(folder_path="Transcript"):
    """Get all txt files in the transcript folder"""
    transcript_files = []
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for file in os.listdir(folder_path):
            if file.endswith(".txt"):
                # Skip files in the old folder if we're searching in Transcript
                if folder_path == "Transcript" and "old" in file:
                    continue
                transcript_files.append(os.path.join(folder_path, file))
    return transcript_files

def split_transcript_by_paragraphs(transcript_path):
    """Split transcript file into paragraphs"""
    with open(transcript_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split by double newlines to separate paragraphs
    paragraphs = re.split(r'\n\s*\n', content.strip())
    return paragraphs

def save_paragraphs(paragraphs, original_filename, output_folder="Transcript"):
    """Save each paragraph as a separate file with UUID"""
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Get base filename without extension and directory
    base_name = os.path.basename(original_filename).rsplit('.', 1)[0]
    
    saved_files = []
    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():  # Skip empty paragraphs
            # Generate UUID
            unique_id = str(uuid.uuid4())
            
            # Create new filename with iterator, UUID, then original name
            # Add 1 to i to start counting from 1 instead of 0
            new_filename = f"{i+1:03d}_{unique_id}_{base_name}.txt"
            new_filepath = os.path.join(output_folder, new_filename)
            
            # Save paragraph to new file
            with open(new_filepath, 'w', encoding='utf-8') as file:
                file.write(paragraph.strip())
            
            saved_files.append(new_filepath)
            print(f"Created file: {new_filename}")
    
    return saved_files

def process_all_transcripts():
    """Process all transcript files"""
    transcript_files = get_transcript_files()
    
    if not transcript_files:
        print("No transcript files found in the Transcript folder.")
        return
    
    # Create old folder if it doesn't exist
    old_folder = os.path.join("Transcript", "old")
    if not os.path.exists(old_folder):
        os.makedirs(old_folder)
    
    total_paragraphs = 0
    for transcript_file in transcript_files:
        print(f"\nProcessing: {transcript_file}")
        paragraphs = split_transcript_by_paragraphs(transcript_file)
        saved_files = save_paragraphs(paragraphs, transcript_file)
        total_paragraphs += len(saved_files)
        print(f"Created {len(saved_files)} paragraph files from {os.path.basename(transcript_file)}")
        
        # Move the original transcript file to the old folder
        try:
            filename = os.path.basename(transcript_file)
            destination = os.path.join(old_folder, filename)
            shutil.move(transcript_file, destination)
            print(f"Moved original file to: {destination}")
        except Exception as e:
            print(f"Error moving original file: {e}")
    
    print(f"\nTotal processing complete. Created {total_paragraphs} paragraph files.")

if __name__ == "__main__":
    process_all_transcripts()
