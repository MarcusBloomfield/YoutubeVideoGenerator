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


def generate_transcript_section(section_type, topic, subtopics=None, model=ModelCategories.getWriteTranscriptModel()):
    """
    Generate a specific section of the transcript (intro, body paragraph, or conclusion)
    
    Args:
        section_type: The type of section to generate ("intro", "body", or "conclusion")
        topic: The main topic
        subtopics: List of subtopics (only used for conclusion)
        model: The OpenAI model to use
        
    Returns:
        Generated section text
    """

    relevant_research = ""
    try:
        if section_type == "intro":
            relevant_research = find_relevant_research(topic)
            prompt = f"""
            Create an engaging introduction for a YouTube video about {topic} during World War II using {relevant_research}.
            Requirements:
            - Set the historical context
            - Capture viewer interest
            - Preview what will be covered in the video
            - Length: 500 words
            - Format: Single paragraph optimized for narration
            - No section headers or formatting
            """
        elif section_type == "body":
            relevant_research = find_relevant_research(topic)

            if not subtopics:
                return ""
            
            prompt = f"""
            Create an informative body paragraph for a YouTube video about {topic} during World War II, 
            focusing specifically on the subtopic: {subtopics} using {relevant_research}.
            
            Requirements:
            - Provide detailed information about this specific subtopic
            - Include relevant dates, figures, and events
            - Discuss military strategies and decisions if applicable
            - Include personal stories if applicable
            - Length: 1000 words
            - Format: Single paragraph optimized for narration
            - No section headers or formatting
            """
        elif section_type == "conclusion":
            subtopics_text = ", ".join(subtopics) if subtopics else "various aspects of the topic"
            
            prompt = f"""
            Create a conclusion for a YouTube video about {topic} during World War II that summarizes 
            the following subtopics: {subtopics_text}.
            
            Requirements:
            - Summarize key points covered (the subtopics)
            - Discuss historical significance and impact
            - Provide a thought-provoking closing statement
            - Length: 500 words
            - Format: Single paragraph optimized for narration
            - No section headers or formatting
            """
        
        # Query OpenAI to generate the section
        section_text = query_openai(prompt, model=model)
        
        if not section_text:
            print(f"[ERROR] No response from OpenAI API for {section_type} section")
            return ""
            
        return section_text
        
    except Exception as e:
        print(f"[ERROR] Error generating {section_type} section: {e}")
        return ""

def generate_transcript(topic="History", subtopics=None, model=ModelCategories.getWriteTranscriptModel()):
    """
    Generate a structured transcript with intro, body paragraphs, and conclusion
    
    Args:
        topic: The main topic to focus on
        subtopics: List of subtopics for body paragraphs
        model: The OpenAI model to use
        
    Returns:
        Path to the generated transcript file
    """
    try:
        # If no subtopics provided, use a default set
        if not subtopics:
            print("[INFO] No subtopics provided, using default subtopics")
            subtopics = ["Key events", "Important figures", "Strategic significance"]
        
        print(f"[INFO] Generating transcript for topic: {topic}")
        print(f"[INFO] Subtopics: {', '.join(subtopics)}")
        
        # Create output directory if it doesn't exist
        output_dir = "Transcript"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        filename = f"ww2_{topic.lower().replace(' ', '_')}_transcript.txt"
        transcript_path = os.path.join(output_dir, filename)
        
        # Create the file immediately to start writing incrementally
        with open(transcript_path, 'w', encoding='utf-8') as f:
            # Generate intro
            print("[INFO] Generating introduction...")
            intro = generate_transcript_section("intro", topic, model=model)
            f.write(intro + "\n\n")
            print("[INFO] Introduction written to file")
            
            # Generate body paragraphs
            for subtopic in subtopics:
                print(f"[INFO] Generating body paragraph for subtopic: {subtopic}")
                body = generate_transcript_section("body", topic, subtopic, model=model)
                f.write(body + "\n\n")
                print(f"[INFO] Body paragraph for {subtopic} written to file")
            
            # Generate conclusion
            print("[INFO] Generating conclusion...")
            conclusion = generate_transcript_section("conclusion", topic, subtopics, model=model)
            f.write(conclusion)
            print("[INFO] Conclusion written to file")
            
        print(f"[OK] Generated transcript saved to: {transcript_path}")
        return transcript_path
        
    except Exception as e:
        print(f"[ERROR] Error generating transcript: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate a World War 2 video transcript with structured sections")
    parser.add_argument("--topic", type=str, default="History", help="Main topic to focus on")
    parser.add_argument("--subtopics", type=str, nargs="+", help="Subtopics for body paragraphs")
    parser.add_argument("--model", type=str, default=ModelCategories.getWriteTranscriptModel(), help="OpenAI model to use")
    
    args = parser.parse_args()
    
    # Prompt for subtopics if not provided via command line
    subtopics = args.subtopics
    if not subtopics:
        print(f"Enter subtopics for {args.topic} (comma-separated):")
        subtopics_input = input("> ")
        subtopics = [s.strip() for s in subtopics_input.split(",") if s.strip()]
    
    # Generate the transcript
    transcript_file = generate_transcript(args.topic, subtopics, args.model)
    
    if transcript_file:
        print(f"[OK] Successfully generated transcript: {transcript_file}")
    else:
        print("[ERROR] Failed to generate transcript")

if __name__ == "__main__":
    main()

