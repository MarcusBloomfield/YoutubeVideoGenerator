import csv
import re
import os
from pathlib import Path
import ProjectPathManager as paths

# Define paths as constants that can be overridden by YoutubeVideoGeneratorGUI.py
CLIPS_DATA_PATH = paths.get_clips_data_path()

def purify_clips_data():
    input_file = CLIPS_DATA_PATH
    output_file = os.path.join(os.path.dirname(input_file), "clips_data_purified.csv")
    
    # Keywords to filter out (case-insensitive)
    keywords_to_filter = ["dark", "black", "handwriting"]
    
    # Compile regex pattern for case-insensitive matching
    pattern = re.compile(r'(' + '|'.join(keywords_to_filter) + ')', re.IGNORECASE)
    
    # Count the filtered rows
    total_rows = 0
    filtered_rows = 0
    
    # Read the input csv and write to the output csv, filtering out rows
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Write the header row
        header = next(reader)
        writer.writerow(header)
        
        # Process the data rows
        for row in reader:
            total_rows += 1
            
            # Check if any of the keywords are in the keywords field (last column)
            if row and len(row) > 5 and pattern.search(row[5]):
                filtered_rows += 1
                continue  # Skip this row
            
            # Write the row to the output file
            writer.writerow(row)
    
    # Print statistics
    print(f"Processed {total_rows} clips")
    print(f"Filtered out {filtered_rows} clips containing keywords: {', '.join(keywords_to_filter)}")
    print(f"Remaining clips: {total_rows - filtered_rows}")
    print(f"Purified data saved to {output_file}")
    
    # Rename the purified file to replace the original
    os.replace(output_file, input_file)
    print(f"Renamed purified file to {input_file}")
    
    return input_file

if __name__ == "__main__":
    purify_clips_data()
