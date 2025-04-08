import os
import sys
import argparse
import datetime
import requests
from OpenAiQuerying import query_openai, check_api_key
from Prompts import TRANSCRIPT_GENERATION_PROMPT, TRANSCRIPT_WITH_RESEARCH_PROMPT
from Models import ModelCategories

def create_transcript_folder():
    """Create a Transcript folder if it doesn't exist"""
    os.makedirs("Transcript", exist_ok=True)
    print("[OK] Transcript folder ready")

def get_research_files(topic):
    """Get content from relevant research files in the Research folder"""
    research_content = ""
    research_dir = "Research"
    
    # Check if Research directory exists
    if not os.path.isdir(research_dir):
        print("[INFO] No Research directory found")
        return research_content
    
    # List all text files in the Research directory
    research_files = [f for f in os.listdir(research_dir) if f.endswith(".txt")]
    
    if not research_files:
        print("[INFO] No research files found in Research directory")
        return research_content
    
    # Check for topic-specific research files first
    topic_keywords = topic.lower().split()
    relevant_files = []
    
    for file in research_files:
        file_lower = file.lower()
        # Check if any keyword from the topic is in the filename
        if any(keyword in file_lower for keyword in topic_keywords):
            relevant_files.append(file)
    
    # If no topic-specific files found, use all txt files
    if not relevant_files:
        print(f"[INFO] No topic-specific research files found for '{topic}', using all available research")
        relevant_files = research_files
    
    # Read content from relevant files
    for file in relevant_files:
        file_path = os.path.join(research_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                research_content += f"\n\n--- Research from {file} ---\n\n{content}"
                print(f"[OK] Added research content from: {file}")
        except Exception as e:
            print(f"[ERROR] Failed to read research file {file}: {e}")
    
    return research_content

def generate_transcript(topic="History", model=ModelCategories.getWriteTranscriptModel()):
    """
    Generate a transcript for a World War 2 video
    
    Args:
        topic: The specific topic to focus on
        model: The OpenAI model to use
        
    Returns:
        Path to the generated transcript file
    """
    try:
        # Create prompt for transcript generation
        prompt = TRANSCRIPT_GENERATION_PROMPT.format(topic=topic)
        
        # Query OpenAI to generate the transcript
        transcript = query_openai(prompt, model=model)
        
        if not transcript:
            print("Error: No response from OpenAI API")
            return None
            
        # Create output directory if it doesn't exist
        output_dir = "Transcripts"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        filename = f"ww2_{topic.lower().replace(' ', '_')}_transcript.txt"
        transcript_path = os.path.join(output_dir, filename)
        
        # Save the generated transcript
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
            
        print(f"Generated transcript saved to: {transcript_path}")
        return transcript_path
        
    except Exception as e:
        print(f"Error generating transcript: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate a World War 2 video transcript")
    parser.add_argument("--topic", type=str, default="History", help="Specific topic to focus on")
    parser.add_argument("--model", type=str, default=ModelCategories.getDefaultModel(), help="OpenAI model to use")
    
    args = parser.parse_args()
    
    # Generate the transcript
    transcript_file = generate_transcript(args.topic, args.model)
    
    if transcript_file:
        print(f"Successfully generated transcript: {transcript_file}")
    else:
        print("Failed to generate transcript")

if __name__ == "__main__":
    main()

