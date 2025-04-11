import os
import csv
import re
import ProjectPathManager as paths

# Define constant paths that can be overridden by YoutubeVideoGeneratorGUI.py
TRANSCRIPT_DIR = paths.get_transcript_dir()
OUTPUT_CSV = paths.get_transcripts_data_path()

def parse_filename(filename):
    # Update regex to match format with multiple underscores in location: ORDER_ID_LOCATION_PART1_LOCATION_PART2_transcript.txt
    pattern = r'(\d+)_([a-f0-9-]+)_(.+)_transcript\.txt'
    match = re.match(pattern, filename)
    
    if match:
        order = match.group(1)
        transcript_id = match.group(2)
        location = match.group(3)
        # Since there is no date in the filename, use a default or current date
        date = "20230101"  # Default date as placeholder
        return order, transcript_id, date, location
    return None, None, None, None

def main():
    # Folder containing the transcripts
    transcripts_folder = TRANSCRIPT_DIR
    
    # Output CSV file
    output_csv = OUTPUT_CSV
    
    # Check if the Transcripts folder exists
    if not os.path.exists(transcripts_folder):
        print(f"Error: {transcripts_folder} directory not found")
        return
    
    # Check if CSV file already exists and load existing transcript IDs
    existing_transcripts = set()
    if os.path.exists(output_csv):
        with open(output_csv, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            # Skip header row and get all transcript IDs from column 1
            next(csv_reader, None)  # Skip header
            existing_transcripts = {row[1] for row in csv_reader if len(row) > 1}
            print(f"Found {len(existing_transcripts)} existing transcripts in CSV")
        
        # Clear existing data, but still track transcript IDs to avoid duplicates
        print(f"Clearing existing data from {output_csv}")
    
    # Start with fresh CSV data (header only)
    csv_data = [["order", "id", "date", "location", "length", "audio_file", "transcript_file"]]
    
    # Track new transcripts added
    new_transcripts_count = 0
    
    # Process each file in the Transcripts folder
    for filename in os.listdir(transcripts_folder):
        if filename.endswith(".txt") and os.path.isfile(os.path.join(transcripts_folder, filename)):
            file_path = os.path.join(transcripts_folder, filename)
            
            # Parse filename to extract metadata
            order, transcript_id, date, location = parse_filename(filename)
            
            if transcript_id:
                # Skip if transcript already exists in CSV
                if transcript_id in existing_transcripts:
                    print(f"Skipping existing transcript: {filename}")
                    continue
                
                # Format date (assuming YYYYMMDD format in filename)
                try:
                    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                except:
                    formatted_date = date
                
                # Add to CSV data with empty length field that can be filled later
                # Include the transcript file path
                csv_data.append([order, transcript_id, formatted_date, location, "", "", file_path])
                new_transcripts_count += 1
            else:
                print(f"Warning: Could not parse filename: {filename}")
    
    # Write to CSV file
    with open(output_csv, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(csv_data)
    
    print(f"CSV file updated: {output_csv}")
    print(f"New transcripts added: {new_transcripts_count}")
    print(f"Total transcripts in CSV: {len(csv_data) - 1}")

if __name__ == "__main__":
    main()
