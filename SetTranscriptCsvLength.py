import csv
import os
import librosa

def get_audio_duration(audio_file_path):
    """Get the duration of an audio file in seconds using librosa."""
    try:
        if os.path.exists(audio_file_path):
            duration = librosa.get_duration(path=audio_file_path)
            return round(duration, 2)
        else:
            print(f"Audio file not found: {audio_file_path}")
            return None
    except Exception as e:
        print(f"Error processing {audio_file_path}: {e}")
        return None

def update_csv_with_audio_lengths(csv_file_path):
    """Update the length column in the CSV with audio file durations."""
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
    csv_file_path = "transcripts_data.csv"
    update_csv_with_audio_lengths(csv_file_path)
    print("CSV update complete")
