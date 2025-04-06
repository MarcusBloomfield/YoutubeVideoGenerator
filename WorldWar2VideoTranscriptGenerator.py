import os
import argparse
import datetime
from OpenAiQuerying import query_openai, check_api_key

def create_transcript_folder():
    """Create a Transcript folder if it doesn't exist"""
    os.makedirs("Transcript", exist_ok=True)
    print("[OK] Transcript folder ready")

def generate_transcript(topic, model="gpt-4o-mini"):
    """Generate a transcript for a YouTube video about a World War 2 battle"""
    
    # Check if API key is available
    api_key = check_api_key()
    if not api_key:
        print("Please set your OPENAI_API_KEY in environment variables or .env file")
        return
    
    print(f"Generating transcript for: {topic}")
    
    # Create a detailed prompt for the AI
    prompt = f"""
    Create a detailed historical transcript for a YouTube video about {topic} during World War II.
    
    The transcript should:
    - Begin with an engaging introduction about the historical context
    - Cover key events in chronological order
    - Explain military strategies and tactical decisions
    - Include personal stories or accounts from soldiers involved
    - Mention the impact and significance of this battle
    - End with a meaningful conclusion about the battle's legacy
    
    Format as a single cohesive block of text optimized for text-to-speech narration.
    Use clear transitions between topics and maintain an engaging, educational tone.
    Include specific dates, locations, key figures, and accurate historical details.
    Aim for approximately 800-1000 words of rich, detailed content.
    """
    
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
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI model to use")
    
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
