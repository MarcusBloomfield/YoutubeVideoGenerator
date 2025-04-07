import os
import csv
import re
import datetime

def parse_filename(filename):
    # Regex pattern to extract info from filename format: UUID_DATE_LOCATION_LENGTH.mp4
    pattern = r'([a-f0-9-]+)_(\d+)_([A-Za-z]+)_(\d+\.\d+)\.mp4'
    match = re.match(pattern, filename)
    
    if match:
        clip_id = match.group(1)
        date = match.group(2)
        location = match.group(3)
        length = float(match.group(4))
        return clip_id, date, location, length
    return None, None, None, None

def main():
    # Folder containing the clips
    clips_folder = "Clips"
    
    # Output CSV file
    output_csv = "clips_data.csv"
    
    # Check if the Clips folder exists
    if not os.path.exists(clips_folder):
        print(f"Error: {clips_folder} directory not found")
        return
    
    # Check if CSV file already exists and load existing clip IDs
    existing_clips = set()
    existing_data = []
    if os.path.exists(output_csv):
        with open(output_csv, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            existing_data = list(csv_reader)
            # Skip header row and get all clip IDs from column 0
            if len(existing_data) > 0:
                existing_clips = {row[0] for row in existing_data[1:]}
                print(f"Found {len(existing_clips)} existing clips in CSV")
    
    # Prepare CSV data
    if existing_data:
        csv_data = existing_data
    else:
        csv_data = [["id", "date", "location", "length", "filelocation", "keywords"]]
    
    # Track new clips added
    new_clips_count = 0
    
    # Process each file in the Clips folder
    for filename in os.listdir(clips_folder):
        if filename.endswith(".mp4"):
            file_path = os.path.join(clips_folder, filename)
            
            # Parse filename to extract metadata
            clip_id, date, location, length = parse_filename(filename)
            
            if clip_id:
                # Skip if clip already exists in CSV
                if clip_id in existing_clips:
                    print(f"Skipping existing clip: {filename}")
                    continue
                
                # Format date (assuming YYYYMMDD format in filename)
                try:
                    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                except:
                    formatted_date = date
                
                # Add to CSV data with empty keywords field that can be filled later
                csv_data.append([clip_id, formatted_date, location, str(length), file_path, ""])
                new_clips_count += 1
            else:
                print(f"Warning: Could not parse filename: {filename}")
    
    # Write to CSV file
    with open(output_csv, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(csv_data)
    
    print(f"CSV file updated: {output_csv}")
    print(f"New clips added: {new_clips_count}")
    print(f"Total clips in CSV: {len(csv_data) - 1}")

if __name__ == "__main__":
    main()
