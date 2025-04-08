import os
import sys
import time
from OpenAiQuerying import query_openai, check_api_key
from prompts import EXPAND_TRANSCRIPT_PROMPT, EXPAND_TRANSCRIPT_WITH_RESEARCH_PROMPT, RESEARCH_MATCHING_PROMPT

def count_words(text):
    """Count the number of words in a text"""
    return len(text.split())

def find_relevant_research(transcript_text, research_dir="Research"):
    """
    Find relevant research materials for expanding the transcript using OpenAI's semantic matching
    
    Args:
        transcript_text: The transcript text to find relevant research for
        research_dir: Directory containing research files
        
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
    
    # Process each research file individually
    relevant_research = []
    for filename in research_files:
        file_path = os.path.join(research_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Create prompt for this specific research file
            prompt = RESEARCH_MATCHING_PROMPT.format(
                transcript=transcript_text,
                research_materials=f"--- RESEARCH: {filename} ---\n{content}"
            )
            
            try:
                # Query OpenAI for relevant content from this file
                file_relevant_content = query_openai(prompt, model="gpt-4o-mini")
                if file_relevant_content:
                    relevant_research.append(f"--- RESEARCH: {filename} ---\n{file_relevant_content}")
                    print(f"Found relevant content in {filename}")
            except Exception as e:
                print(f"Error processing research file {filename}: {e}")
    
    if relevant_research:
        print("Successfully found relevant research using semantic matching")
        return "\n\n".join(relevant_research)
    else:
        print("No relevant research found in any files")
        return ""

def expand_transcript(transcript_path, target_loops=5, model="gpt-4o", words_needed=1000):
    """
    Expand a transcript through a specified number of expansion loops using research materials
    
    Args:
        transcript_path: Path to the transcript file
        target_loops: Number of expansion loops to perform
        model: OpenAI model to use
    
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

        if expansion_round == 1 or expansion_round % 5 == 0:
            # Find relevant research materials
            research_content = find_relevant_research(current_transcript)
    
            if not research_content:
                print("Error: No relevant research found. Cannot expand transcript without research materials.")
                return current_transcript
        # Craft prompt for expansion that includes research materials
        prompt = EXPAND_TRANSCRIPT_WITH_RESEARCH_PROMPT.format(
            words_needed=words_needed,  # Fixed word target per expansion
            current_transcript=current_transcript,
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
            time.sleep(10)  # 10 second pause
    
    print(f"Final word count: {current_word_count}")
    return current_transcript

def process_all_transcripts(transcript_dir="Transcript", target_loops=5, research_dir="Research"):
    """Process all transcript files in the given directory"""
    # Ensure API key is available
    api_key = check_api_key()
    if not api_key:
        print("Error: OpenAI API key not found")
        return
        
    print(f"Processing all transcripts in {transcript_dir} with {target_loops} expansion loops each")
    print(f"Using research materials from {research_dir}")
    
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
        expand_transcript(transcript_path, target_loops)
        print(f"Completed expansion of {filename}")
        print("-" * 50)

if __name__ == "__main__":
    # Default directory and target loops
    transcript_dir = "Transcript"
    target_loops = 5
    research_dir = "Research"
    
    # Allow command line override
    if len(sys.argv) > 1:
        transcript_dir = sys.argv[1]
    if len(sys.argv) > 2:
        target_loops = int(sys.argv[2])
    if len(sys.argv) > 3:
        research_dir = sys.argv[3]
    
    process_all_transcripts(transcript_dir, target_loops, research_dir)
