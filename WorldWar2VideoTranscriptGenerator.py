import os
import argparse
import datetime
import requests
from OpenAiQuerying import query_openai, check_api_key
from prompts import TRANSCRIPT_GENERATION_PROMPT, TRANSCRIPT_WITH_RESEARCH_PROMPT

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

def generate_transcript(topic="Iwo Jima", model="gpt-4o-mini"):
    """Generate a transcript for a YouTube video about a World War 2 battle"""
    
    # Check if API key is available
    api_key = check_api_key()
    if not api_key:
        print("Please set your OPENAI_API_KEY in environment variables or .env file")
        return
    
    print(f"Generating transcript for: {topic}")
    
    # Get research content from relevant files
    research_content = get_research_files(topic)
    
    # Create a detailed prompt for the AI
    if not research_content:
        prompt = TRANSCRIPT_GENERATION_PROMPT.format(topic=topic)
    else:
        prompt = TRANSCRIPT_WITH_RESEARCH_PROMPT.format(
            topic=topic,
            research_content=research_content
        )
    
    # Query OpenAI for the transcript
    transcript = query_openai(prompt, model=model, api_key=api_key)
    
    if transcript:
        # Create a filename with date and battle name
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        safe_battle_name = topic.replace(" ", "_").replace("/", "_")
        filename = f"Transcript/{timestamp}_{safe_battle_name}.txt"
        
        # Save the transcript to a file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        print(f"[OK] Transcript saved to: {filename}")
        return filename
    else:
        print("[ERROR] Failed to generate transcript")
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate World War 2 battle transcripts for YouTube videos")
    parser.add_argument("--topic", type=str, help="Name of the World War 2 battle or topic")
    parser.add_argument("--model", type=str, default="gpt-4o", help="OpenAI model to use")
    
    args = parser.parse_args()
    
    # Create transcript folder
    create_transcript_folder()
    
    # Get battle name from command line or prompt
    topic = args.topic
    if not topic:
        topic = input("Enter the name of the World War 2 battle or topic: ")
    
    # Generate and save the transcript
    transcript_file = generate_transcript(topic, model=args.model)
    
    if transcript_file:
        print(f"Transcript generation complete. File saved at: {transcript_file}")

if __name__ == "__main__":
    main()

