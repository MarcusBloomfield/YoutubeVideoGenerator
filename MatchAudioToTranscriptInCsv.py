import os
import csv
import re
import ProjectPathManager as paths

def match_audio_to_transcript(csv_file=None, audio_folder=None):
    # Define paths
    audio_folder = audio_folder or paths.get_audio_dir()
    csv_file = csv_file or paths.get_transcripts_data_path()
    
    # Get list of audio files
    audio_files = os.listdir(audio_folder)
    
    # Read CSV file
    csv_data = []
    with open(csv_file, 'r', newline='') as file:
        reader = csv.DictReader(file)
        csv_data = list(reader)
    
    # Match audio files to transcript entries
    matches = 0
    for row in csv_data:
        transcript_id = row['id']
        
        # Find matching audio file
        for audio_file in audio_files:
            # Extract ID from filename using regex
            match = re.search(r'_(' + transcript_id + r')_', audio_file)
            if match or transcript_id in audio_file:
                # Update the audio_file column
                row['audio_file'] = os.path.join(audio_folder, audio_file)
                matches += 1
                break
    
    # Write updated data back to CSV
    with open(csv_file, 'w', newline='') as file:
        fieldnames = csv_data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"Matched {matches} audio files to transcript entries.")
    return matches

if __name__ == "__main__":
    match_audio_to_transcript()
