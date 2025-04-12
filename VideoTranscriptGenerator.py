import os
import sys
import argparse
import datetime
import requests
from OpenAiQuerying import query_openai, check_api_key
from Prompts import TRANSCRIPT_GENERATION_PROMPT, TRANSCRIPT_WITH_RESEARCH_PROMPT, RESEARCH_MATCHING_PROMPT
from Models import ModelCategories
from ExpandTranscript import find_relevant_research

def create_transcript_folder():
    """Create a Transcript folder if it doesn't exist"""
    os.makedirs("Transcript", exist_ok=True)
    print("[OK] Transcript folder ready")


def generate_complete_transcript(topic, relevant_research="", model=ModelCategories.getWriteTranscriptModel()):
    """
    Generate a complete transcript for a video in one go
    
    Args:
        topic: The main topic
        relevant_research: Any relevant research to incorporate
        model: The OpenAI model to use
        
    Returns:
        Generated transcript text
    """
    try:
        prompt = f"""
       {topic} in 1000 words using {relevant_research}.
        
        Requirements:
        - Format: Paragraphs optimized for narration
        - No section headers or formatting
        """
        
        # Query OpenAI to generate the complete transcript
        transcript_text = query_openai(prompt, model=model)
        
        if not transcript_text:
            print("[ERROR] No response from OpenAI API for transcript generation")
            return ""
            
        return transcript_text
        
    except Exception as e:
        print(f"[ERROR] Error generating transcript: {e}")
        return ""

def generate_transcript(topic="History", model=ModelCategories.getWriteTranscriptModel()):
    """
    Generate a complete transcript
    
    Args:
        topic: The main topic to focus on
        model: The OpenAI model to use
        
    Returns:
        Path to the generated transcript file
    """
    try:
        print(f"[INFO] Generating transcript for topic: {topic}")
        
        # Create output directory if it doesn't exist
        output_dir = "Transcript"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        filename = f"ww2_{topic.lower().replace(' ', '_')}_transcript.txt"
        transcript_path = os.path.join(output_dir, filename)
        
        # Find relevant research if available
        print("[INFO] Finding relevant research...")
        relevant_research = find_relevant_research(topic)
        
        # Generate the complete transcript
        print("[INFO] Generating complete transcript...")
        transcript = generate_complete_transcript(topic, relevant_research, model=model)
        
        # Write to file
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        print(f"[OK] Generated transcript saved to: {transcript_path}")
        return transcript_path
        
    except Exception as e:
        print(f"[ERROR] Error generating transcript: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate a World War 2 video transcript")
    parser.add_argument("--topic", type=str, default="History", help="Main topic to focus on")
    parser.add_argument("--model", type=str, default=ModelCategories.getWriteTranscriptModel(), help="OpenAI model to use")
    
    args = parser.parse_args()
    
    # Generate the transcript
    transcript_file = generate_transcript(args.topic, args.model)
    
    if transcript_file:
        print(f"[OK] Successfully generated transcript: {transcript_file}")
    else:
        print("[ERROR] Failed to generate transcript")

if __name__ == "__main__":
    main()

