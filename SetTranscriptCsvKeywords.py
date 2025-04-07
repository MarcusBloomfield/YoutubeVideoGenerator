import os
import csv
from OpenAiQuerying import query_openai, check_api_key

def get_all_unique_keywords_from_clips():
    """
    Extract all unique keywords from clips_data.csv
    
    Returns:
        list: List of unique keywords
    """
    clips_csv_file = "clips_data.csv"
    all_keywords = set()
    
    try:
        with open(clips_csv_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if 'keywords' in row and row['keywords']:
                    # Split by comma and remove spaces
                    keywords = [k.strip() for k in row['keywords'].replace('"', '').split(',')]
                    for keyword in keywords:
                        all_keywords.add(keyword)
        
        return sorted(list(all_keywords))
    
    except Exception as e:
        print(f"Error reading clips_data.csv: {e}")
        return []

def generate_keywords_for_transcript(transcript_text):
    """
    Generate keywords for a transcript using OpenAI.
    
    Args:
        transcript_text (str): The transcript text
        
    Returns:
        str: Comma-separated keywords
    """
    # Get all available keywords from clips
    available_keywords = get_all_unique_keywords_from_clips()
    
    prompt = f"""
    Based on the following transcript, select 5-10 relevant keywords or key phrases from the list of available keywords that best represent what should be in the video during the transcript.
    No abstract ideas or concepts, only specific things that should be in the video.
    
    Available keywords to choose from:
    {', '.join(available_keywords)}
    
    Return ONLY the keywords separated by commas, without any additional text or explanation.
    
    Transcript:
    {transcript_text}
    """
    
    api_key = check_api_key()
    if not api_key:
        print("Error: No OpenAI API key found. Please set OPENAI_API_KEY in your environment variables.")
        return ""
    
    response = query_openai(prompt, api_key=api_key)
    return response.strip() if response else ""

def process_csv():
    """Process the transcripts_data.csv file and update the keywords column"""
    csv_file = "transcripts_data.csv"
    
    try:
        # Read the CSV file
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        # Check if required columns exist
        if 'transcript_file' not in reader.fieldnames or 'keywords' not in reader.fieldnames:
            print(f"Error: CSV file must contain 'transcript_file' and 'keywords' columns")
            return
        
        total_rows = len(rows)
        print(f"Processing {total_rows} transcripts...")
        
        # Update rows
        for i, row in enumerate(rows):
            transcript_file = row['transcript_file']
            
            # Skip if transcript file is empty
            if not transcript_file:
                print(f"Skipping row {i+1}: No transcript file specified")
                continue
            
            # Skip if keywords are already set and not empty
            if row['keywords'] and row['keywords'].strip():
                print(f"Skipping row {i+1}: Keywords already set")
                continue
            
            print(f"Processing row {i+1}/{total_rows}: {transcript_file}")
            
            # Read the transcript file
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
                
                # Generate keywords
                keywords = generate_keywords_for_transcript(transcript_text)
                
                if keywords:
                    # Update the row
                    rows[i]['keywords'] = keywords
                    print(f"Set keywords for {transcript_file}: {keywords}")
                else:
                    print(f"Warning: Failed to generate keywords for {transcript_file}")
            
            except FileNotFoundError:
                print(f"Error: Transcript file not found: {transcript_file}")
            except Exception as e:
                print(f"Error processing {transcript_file}: {e}")
        
        # Write the updated data back to the CSV file
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"CSV file updated successfully: {csv_file}")
    
    except Exception as e:
        print(f"Error processing CSV file: {e}")

if __name__ == "__main__":
    process_csv()
