import os
import sys
import re
import json
import openai
from OpenAiQuerying import query_openai
from Models import ModelCategories
import ProjectPathManager as paths

def count_words(text):
    """Count the number of words in the given text"""
    return len(re.findall(r'\b\w+\b', text))

def expand_transcript(transcript_path, loops=1, model=ModelCategories.getTranscriptExpansionModel(), words_needed=1000):
    """
    Expand a transcript by adding more content
    
    Args:
        transcript_path: Path to the transcript file
        loops: Number of expansion loops to perform
        model: OpenAI model to use
        words_needed: Target word count
        
    Returns:
        Path to the expanded transcript file
    """
    # Read the original transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        original_content = f.read().strip()
    
    print(f"Original transcript word count: {count_words(original_content)}")
    
    # If we already have enough words, just return the original file
    if count_words(original_content) >= words_needed:
        print(f"Transcript already has enough words ({count_words(original_content)} >= {words_needed})")
        return transcript_path
    
    # Determine filename for expanded transcript
    transcript_dir = os.path.dirname(transcript_path)
    if transcript_dir == "":
        transcript_dir = paths.get_transcript_dir()
    
    original_filename = os.path.basename(transcript_path)
    expanded_filename = f"expanded_{original_filename}"
    expanded_path = os.path.join(transcript_dir, expanded_filename)
    
    # Find relevant research if available
    relevant_research = find_relevant_research(original_content)
    
    # Perform expansion loops
    content = original_content
    for i in range(loops):
        print(f"Expansion loop {i+1}/{loops}...")
        
        # Get current word count
        current_words = count_words(content)
        if current_words >= words_needed:
            print(f"Reached target word count ({current_words} >= {words_needed})")
            break
        
        additional_words = words_needed - current_words
        print(f"Adding approximately {additional_words} more words...")
        
        # Create the expansion prompt
        prompt = f"""
        I need you to expand this transcript about World War II with more detailed content. The current word count is {current_words} and I need to add about {additional_words} more words.
        
        Please add more historical details, descriptions, context, and analysis to make the narrative more informative and engaging. Focus on:
        
        1. Adding specific dates, locations, and names of key figures
        2. Explaining military strategy and tactical decisions
        3. Including relevant statistics and numbers
        4. Providing more context about the historical significance of events
        5. Incorporating first-hand accounts or quotes where appropriate
        
        Original transcript:
        ```
        {content}
        ```
        
        Research to incorporate:
        ```
        {relevant_research}
        ```
        
        The expanded transcript should maintain the same overall structure but with significantly more content. 
        Format as a single, cohesive narrative suitable for a YouTube video narration.
        Return ONLY the expanded transcript with no comments or explanations.
        """
        
        # Get the expansion from OpenAI
        expanded_content = query_openai(prompt, model=model)
        
        if not expanded_content or expanded_content.strip() == "":
            print("Warning: Received empty response from OpenAI API. Using original content.")
            expanded_content = content
            
        # Save this iteration of expanded content
        content = expanded_content
        
        # Save the expanded transcript
        with open(expanded_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Expanded transcript saved to: {expanded_path}")
        print(f"New word count: {count_words(content)}")
    
    return expanded_path

def find_relevant_research(content, research_dir=None):
    """Find relevant research for the given content"""
    research_dir = research_dir or paths.get_research_dir()
    
    if not os.path.exists(research_dir):
        print(f"Research directory not found: {research_dir}")
        return ""
    
    # Extract key topics from the content
    topics = extract_topics(content)
    if not topics:
        print("No topics extracted from content")
        return ""
    
    print(f"Extracted topics: {', '.join(topics)}")
    
    # Find research files containing the topics
    relevant_files = []
    for filename in os.listdir(research_dir):
        if filename.endswith(".txt") or filename.endswith(".md"):
            file_path = os.path.join(research_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().lower()
                
                # Check if any topic is in the file content
                matches = [topic for topic in topics if topic.lower() in file_content]
                if matches:
                    relevant_files.append((file_path, len(matches)))
            except Exception as e:
                print(f"Error reading research file {file_path}: {e}")
    
    # Sort by number of matches (descending)
    relevant_files.sort(key=lambda x: x[1], reverse=True)
    
    # Only use top 3 most relevant files to avoid too much content
    relevant_files = relevant_files[:3]
    
    # Combine relevant research content
    combined_research = ""
    for file_path, _ in relevant_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                combined_research += content + "\n\n"
            print(f"Including research from: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error reading research file {file_path}: {e}")
    
    # Limit research size to avoid token limits
    if len(combined_research) > 10000:
        combined_research = combined_research[:10000] + "..."
        print("Research content truncated due to size limits")
        
    return combined_research

def extract_topics(content):
    """Extract key topics from the content using OpenAI"""
    prompt = f"""
    Please extract 5-10 key topics or themes from this World War II transcript. 
    Return only the list of topics as a valid JSON array of strings.
    
    Transcript:
    ```
    {content}
    ```
    """
    
    try:
        response = query_openai(prompt)
        
        # Find anything that looks like a JSON array
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            try:
                topics = json.loads(match.group(0))
                return topics
            except json.JSONDecodeError:
                print(f"Could not parse AI response as JSON: {response}")
                # Fallback to extracting quoted strings
                topics = re.findall(r'"([^"]+)"', response)
                if topics:
                    return topics
        
        # If we can't find proper JSON, just split by newlines and clean up
        topics = [line.strip().strip('"-,').strip() for line in response.split('\n') if line.strip()]
        return [topic for topic in topics if len(topic) > 3 and not topic.startswith('[') and not topic.startswith(']')]
        
    except Exception as e:
        print(f"Error extracting topics: {e}")
        return []

def process_all_transcripts(transcript_dir=None, loops=1, research_dir=None, words_needed=1000):
    """Process all transcript files in the directory"""
    transcript_dir = transcript_dir or paths.get_transcript_dir()
    research_dir = research_dir or paths.get_research_dir()
    
    if not os.path.exists(transcript_dir):
        print(f"Transcript directory not found: {transcript_dir}")
        return
    
    transcript_files = [f for f in os.listdir(transcript_dir) 
                       if f.endswith('.txt') and os.path.isfile(os.path.join(transcript_dir, f))]
    
    if not transcript_files:
        print("No transcript files found")
        return
    
    print(f"Found {len(transcript_files)} transcript files")
    
    for filename in transcript_files:
        if 'expanded_' in filename:
            print(f"Skipping already expanded file: {filename}")
            continue
            
        transcript_path = os.path.join(transcript_dir, filename)
        print(f"\nProcessing: {filename}")
        
        try:
            expanded_path = expand_transcript(
                transcript_path, 
                loops=loops, 
                words_needed=words_needed
            )
            print(f"Expanded to: {os.path.basename(expanded_path)}")
        except Exception as e:
            print(f"Error expanding transcript {filename}: {e}")

if __name__ == "__main__":
    # Default directory and target loops
    transcript_dir = paths.get_transcript_dir()
    target_loops = 1
    research_dir = paths.get_research_dir()
    
    # Allow command line override
    if len(sys.argv) > 1:
        transcript_dir = sys.argv[1]
    if len(sys.argv) > 2:
        target_loops = int(sys.argv[2])
    if len(sys.argv) > 3:
        research_dir = sys.argv[3]
    
    process_all_transcripts(transcript_dir, target_loops, research_dir)
