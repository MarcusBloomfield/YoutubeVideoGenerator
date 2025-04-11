import os
import csv
import subprocess
import json
import ProjectPathManager as paths

def get_audio_duration(file_path):
    """Get the duration of an audio file in seconds using ffprobe."""
    try:
        if not os.path.exists(file_path):
            print(f"Audio file not found: {file_path}")
            return None
            
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', file_path]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        if error:
            print(f"Error getting duration for {file_path}: {error.decode()}")
            return None
            
        data = json.loads(output.decode())
        duration = float(data['format']['duration'])
        return duration
    except Exception as e:
        print(f"Exception getting duration for {file_path}: {str(e)}")
        return None

def update_csv_with_audio_lengths(csv_file_path=None):
    """Update the length column in the CSV with audio file durations."""
    # Use project path if none provided
    csv_file_path = csv_file_path or paths.get_transcripts_data_path()
    
    # Read the CSV file
    rows = []
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    # Update each row with audio length
    for row in rows:
        audio_file = row.get('audio_file')
        if audio_file and audio_file.strip():
            duration = get_audio_duration(audio_file)
            if duration is not None:
                row['length'] = str(duration)
    
    # Write back to CSV
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Updated {sum(1 for row in rows if row.get('length'))} rows with audio lengths")

if __name__ == "__main__":
    csv_file_path = paths.get_transcripts_data_path()
    update_csv_with_audio_lengths(csv_file_path)
    print("CSV update complete")
