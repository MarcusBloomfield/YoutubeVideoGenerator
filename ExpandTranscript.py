import os
import sys
import time
import re
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from OpenAiQuerying import query_openai, check_api_key
from Prompts import EXPAND_TRANSCRIPT_PROMPT, EXPAND_TRANSCRIPT_WITH_RESEARCH_PROMPT, RESEARCH_MATCHING_PROMPT, EXPANSION_IDEA_PROMPT
from Models import ModelCategories

def count_words(text):
    """Count the number of words in a text"""
    return len(text.split())

def find_relevant_research(transcript_text, research_dir="Research", max_workers=4, retry_attempts=2):
    """
    Find relevant research materials for expanding the transcript using OpenAI's semantic matching
    
    Args:
        transcript_text: The transcript text to find relevant research for
        research_dir: Directory containing research files
        max_workers: Maximum number of parallel workers for processing research files
        retry_attempts: Number of retry attempts for API calls
        
    Returns:
        A string containing relevant research content
    """
    print(f"Looking for relevant research in {research_dir}...")
    
    if not os.path.exists(research_dir):
        print(f"Research directory {research_dir} not found")
        return ""
        
    # Get all text files in the research directory
    research_files = [f for f in os.listdir(research_dir) 
                     if f.endswith('.txt') and os.path.isfile(os.path.join(research_dir, f))]
    
    if not research_files:
        print(f"No research files found in {research_dir}")
        return ""
        
    print(f"Found {len(research_files)} research files")
    
    # Extract keywords from transcript for basic relevance filtering
    # Get the top ~20 most significant words by removing common words and taking words of 4+ chars
    transcript_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', transcript_text.lower()))
    common_words = {'this', 'that', 'with', 'from', 'have', 'what', 'your', 'they', 'will', 'about', 'when', 'there'}
    transcript_keywords = transcript_words - common_words
    
    # Process research files in parallel
    relevant_research = []
    
    def process_file(filename):
        """Process a single research file and return relevant content if found"""
        file_path = os.path.join(research_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic keyword filtering before sending to OpenAI
            content_lower = content.lower()
            keyword_matches = sum(1 for keyword in transcript_keywords if keyword in content_lower)
            keyword_density = keyword_matches / max(1, len(transcript_keywords))
            
            # Skip files with very low keyword matches (threshold can be adjusted)
            if keyword_density < 0.1 and len(transcript_keywords) > 5:
                print(f"Skipping {filename} - low keyword relevance")
                return None
                
            # Create prompt for this specific research file
            print(f"Processing research file: {filename}")
            prompt = RESEARCH_MATCHING_PROMPT.format(
                transcript=transcript_text,
                research_materials=f"--- RESEARCH: {filename} ---\n{content}",
            )
            
            # Query OpenAI with retry logic
            for attempt in range(retry_attempts + 1):
                try:
                    print(f"Querying OpenAI for relevant content from {filename}")
                    file_relevant_content = query_openai(prompt, model=ModelCategories.getDefaultModel())
                    if file_relevant_content:
                        print(f"Found relevant content in {filename}")
                        print(f"Content: {file_relevant_content[:200]}...")
                        return f"--- RESEARCH: {filename} ---\n{file_relevant_content}"
                    break
                except Exception as e:
                    if attempt < retry_attempts:
                        print(f"Error on attempt {attempt+1} for {filename}: {e}. Retrying...")
                        time.sleep(2)  # Add delay before retry
                    else:
                        print(f"Error processing research file {filename} after {retry_attempts} retries: {e}")
            
            return None
        except Exception as e:
            print(f"Error reading research file {filename}: {e}")
            return None
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_file, filename): filename for filename in research_files}
        for future in as_completed(future_to_file):
            result = future.result()
            if result:
                relevant_research.append(result)
    
    if relevant_research:
        print(f"Successfully found relevant research in {len(relevant_research)} files using semantic matching")
        return "\n\n".join(relevant_research)
    else:
        print("No relevant research found in any files")
        return ""

def expand_transcript(transcript_path, target_loops=5, model=ModelCategories.getResearchModel(), words_needed=1000):
    """
    Expand a transcript through a specified number of expansion loops using research materials
    
    Args:
        transcript_path: Path to the transcript file
        target_loops: Number of expansion loops to perform
        model: OpenAI model to use
        words_needed: Target number of words for expansion
    
    Returns:
        The expanded transcript text
    """
    print(f"Processing transcript: {transcript_path}")
    
    # Read the original transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        original_transcript = f.read().strip()
    
    # Start with the original transcript
    current_transcript = original_transcript
    current_word_count = count_words(current_transcript)
    print(f"Original word count: {current_word_count}")
    
    # Perform the specified number of expansion loops
    for expansion_round in range(1, target_loops + 1):
        print(f"Starting expansion round {expansion_round} of {target_loops}")
        research_content = ""
        try:
            # Find research directly related to the transcript
            research_content = find_relevant_research(current_transcript)
            
            if not research_content:
                print("Warning: No relevant research found for transcript. Will attempt expansion without research.")
        except Exception as e:
            print(f"Error finding relevant research: {e}")
            research_content = ""
        
        # Craft prompt for expansion that includes research materials
        prompt = EXPAND_TRANSCRIPT_WITH_RESEARCH_PROMPT.format(
            current_transcript=current_transcript,
            words_needed=words_needed,
            research_content=research_content
        )
        
        try:
            # Query OpenAI to rewrite and expand the text
            expanded_transcript = query_openai(prompt, model=model)
            
            if expanded_transcript:
                # Replace current transcript with the expanded version
                current_transcript = expanded_transcript
                
                # Update word count
                current_word_count = count_words(current_transcript)
                print(f"Current word count after round {expansion_round}: {current_word_count}")
                
                # Save the expanded transcript at each step
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(current_transcript)
                
                print(f"Saved expanded transcript to {transcript_path}")
            else:
                print("Error: No response from OpenAI API")
                break
                
        except Exception as e:
            print(f"Error during expansion: {e}")
            break
            
        # Pause between requests to respect rate limits
        if expansion_round < target_loops:
            print("Pausing before next expansion...")
    
    print(f"Final word count: {current_word_count}")
    return current_transcript

def process_all_transcripts(transcript_dir="Transcript", target_loops=1, research_dir="Research", words_needed=1000):
    """Process all transcript files in the given directory"""
    # Ensure API key is available
    api_key = check_api_key()
    if not api_key:
        print("Error: OpenAI API key not found")
        return
        
    print(f"Processing all transcripts in {transcript_dir} with {target_loops} expansion loops each")
    print(f"Using research materials from {research_dir}")
    print(f"Target word count: {words_needed}")
    
    # Get all text files in the transcript directory
    transcript_files = [f for f in os.listdir(transcript_dir) 
                       if f.endswith('.txt') and os.path.isfile(os.path.join(transcript_dir, f))]
    
    if not transcript_files:
        print(f"No transcript files found in {transcript_dir}")
        return
        
    print(f"Found {len(transcript_files)} transcript files")
    
    # Process each transcript
    for filename in transcript_files:
        transcript_path = os.path.join(transcript_dir, filename)
        expand_transcript(transcript_path, target_loops, model=ModelCategories.getExpandTranscriptModel(), words_needed=words_needed)
        print(f"Completed expansion of {filename}")
        print("-" * 50)

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Expand transcripts with AI assistance and research materials')
    parser.add_argument('--transcript-dir', type=str, default="Transcript", help='Directory containing transcript files')
    parser.add_argument('--loops', type=int, default=1, help='Number of expansion loops to perform')
    parser.add_argument('--research-dir', type=str, default="Research", help='Directory containing research materials')
    parser.add_argument('--theme', type=str, help='Theme for the transcript expansion')
    parser.add_argument('--youtube-short', action='store_true', help='Optimize for YouTube Shorts format')
    parser.add_argument('--word-count', type=int, default=1000, help='Target word count for expanded transcript')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Extract values
    transcript_dir = args.transcript_dir
    target_loops = args.loops
    research_dir = args.research_dir
    words_needed = args.word_count
    
    # If theme is provided, print it (can be used in future to customize prompts)
    if args.theme:
        print(f"Using theme: {args.theme}")
    
    # If optimizing for YouTube Shorts, adjust word count if not explicitly set
    if args.youtube_short and '--word-count' not in sys.argv:
        words_needed = 150  # YouTube Shorts typically need shorter content
        print(f"Optimizing for YouTube Shorts with target word count: {words_needed}")
    
    process_all_transcripts(transcript_dir, target_loops, research_dir, words_needed)
