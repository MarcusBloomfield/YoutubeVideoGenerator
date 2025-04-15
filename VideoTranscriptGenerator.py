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


def generate_complete_transcript(topic, relevant_research="", model=ModelCategories.getWriteTranscriptModel(), word_count=1000):
    """
    Generate a complete transcript for a video in one go
    
    Args:
        topic: The main topic
        relevant_research: Any relevant research to incorporate
        model: The OpenAI model to use
        word_count: The desired word count for the transcript (default: 1000)
        
    Returns:
        Generated transcript text
    """
    try:
        prompt = f"""
       {topic} in {word_count} words using {relevant_research}.
        
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

def generate_subtopics(topic, num_subtopics=3, model=ModelCategories.getDefaultModel()):
    """
    Generate subtopics for a structured video essay based on the main topic
    
    Args:
        topic: The main topic to generate subtopics for
        num_subtopics: Number of subtopics to generate (default: 3)
        model: The OpenAI model to use
        
    Returns:
        List of generated subtopics
    """
    try:
        print(f"[INFO] Generating {num_subtopics} subtopics for topic: {topic}")
        
        prompt = f"""
        Generate {num_subtopics} specific subtopics for a video essay about {topic} during World War II.
        
        Requirements:
        - Each subtopic should cover a significant aspect of {topic}
        - Subtopics should be distinct from each other
        - Subtopics should be specific, not general
        - Format: Return ONLY a numbered list with no additional text
        - Each subtopic should be 3-5 words
        
        Example format:
        1. Military Strategy
        2. Civilian Impact
        3. Political Consequences
        """
        
        # Query OpenAI to generate subtopics
        response = query_openai(prompt, model=model)
        
        if not response:
            print("[ERROR] No response from OpenAI API for subtopic generation")
            return []
        
        # Parse the numbered list
        subtopics = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 20)):
                # Remove the number and any leading/trailing whitespace
                subtopic = line.split('.', 1)[1].strip()
                subtopics.append(subtopic)
        
        # Ensure we have the requested number of subtopics
        if len(subtopics) < num_subtopics:
            print(f"[WARNING] Only generated {len(subtopics)} subtopics, fewer than requested {num_subtopics}")
        
        # Limit to the requested number
        subtopics = subtopics[:num_subtopics]
        
        print(f"[OK] Generated {len(subtopics)} subtopics: {', '.join(subtopics)}")
        return subtopics
        
    except Exception as e:
        print(f"[ERROR] Error generating subtopics: {e}")
        return []

def generate_transcript_section(section_type, topic, subtopics=None, relevant_research="", full_transcript="", model=ModelCategories.getWriteTranscriptModel(), previous_section=""):
    """
    Generate a specific section of a structured video essay transcript
    
    Args:
        section_type: The type of section ("intro", "body", or "conclusion")
        topic: The main topic
        subtopics: List of subtopics (for body sections) or used in conclusion
        relevant_research: Any relevant research to incorporate
        full_transcript: Current accumulated transcript content
        model: The OpenAI model to use
        previous_section: Content of the previous section (for creating smooth transitions)
        
    Returns:
        Generated section text
    """
    try:
        if section_type == "intro":
            prompt = f"""
            Create an engaging introduction for a YouTube video about {topic} during World War II using {relevant_research}.
            Requirements:
            - Set the historical context
            - Short and concise
            - Get straight to the point
            - Format: Single paragraph optimized for narration
            - No section headers or formatting
            - Length: Around 50 words
            
            Current full transcript: {full_transcript}
            """
        elif section_type == "body":
            if not subtopics:
                return ""
            
            transition_instruction = ""
            if previous_section:
                # Extract the last few sentences (up to 150 characters) for transition context
                transition_context = previous_section[-200:] if len(previous_section) > 200 else previous_section
                transition_instruction = f"""
                Create a smooth transition from the previous paragraph which ended with:
                "{transition_context}"
                """
            
            prompt = f"""
            Create an informative body paragraph for a YouTube video about {topic} during World War II, 
            focusing specifically on the subtopic: {subtopics} using {relevant_research}.
            
            Requirements:
            - Provide detailed information about this specific subtopic
            - Include relevant dates, figures, and events
            - Discuss military strategies and decisions if applicable
            - Include personal stories if applicable
            - Format: Single paragraph optimized for narration
            - Length: Around 300 words
            - No section headers or formatting
            {transition_instruction}
            
            Current full transcript: {full_transcript}
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
            - Format: Single paragraph optimized for narration
            - No section headers or formatting
            
            Current full transcript: {full_transcript}
            """
        else:
            return ""
        
        # Query OpenAI to generate the section
        section_text = query_openai(prompt, model=model)
        
        if not section_text:
            print(f"[ERROR] No response from OpenAI API for {section_type} generation")
            return ""
            
        return section_text
        
    except Exception as e:
        print(f"[ERROR] Error generating {section_type}: {e}")
        return ""

def generate_structured_transcript(topic, subtopics=None, model=ModelCategories.getWriteTranscriptModel(), num_subtopics=3, skip_research=False):
    """
    Generate a structured transcript with intro, body paragraphs, and conclusion
    
    Args:
        topic: The main topic to focus on
        subtopics: List of subtopics for body paragraphs (if None, will auto-generate)
        model: The OpenAI model to use
        num_subtopics: Number of subtopics to auto-generate if subtopics is None
        skip_research: If True, skip finding relevant research
        
    Returns:
        Path to the generated transcript file
    """
    try:
        print(f"[INFO] Generating structured transcript for topic: {topic}")
        
        # Create output directory if it doesn't exist
        output_dir = "Transcript"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        filename = f"ww2_{topic.lower().replace(' ', '_')}_structured_transcript.txt"
        transcript_path = os.path.join(output_dir, filename)
        
        # Find relevant research if not skipped
        relevant_research = ""
        if not skip_research:
            print("[INFO] Finding relevant research...")
            relevant_research = find_relevant_research(topic)
        else:
            print("[INFO] Skipping research as requested")
        
        # Auto-generate subtopics if not provided
        if not subtopics:
            print(f"[INFO] Auto-generating {num_subtopics} subtopics...")
            subtopics = generate_subtopics(topic, num_subtopics, model)
            if not subtopics:
                print("[WARNING] Failed to generate subtopics. Proceeding with generic subtopics.")
                subtopics = ["Historical Background", "Key Figures", "Military Operations"]
        
        # Initialize full transcript
        full_transcript = ""
        previous_section = ""
        
        # Generate introduction
        print("[INFO] Generating introduction...")
        intro = generate_transcript_section("intro", topic, None, relevant_research, full_transcript, model)
        full_transcript += intro + "\n\n"
        previous_section = intro
        
        # Generate body paragraphs for each subtopic
        if subtopics:
            print(f"[INFO] Generating {len(subtopics)} body paragraphs...")
            for subtopic in subtopics:
                body_paragraph = generate_transcript_section("body", topic, subtopic, relevant_research, full_transcript, model, previous_section)
                full_transcript += body_paragraph + "\n\n"
                previous_section = body_paragraph
        
        # Generate conclusion
        print("[INFO] Generating conclusion...")
        conclusion = generate_transcript_section("conclusion", topic, subtopics, relevant_research, full_transcript, model, previous_section)
        full_transcript += conclusion
        
        # Write to file
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(full_transcript)
        
        print(f"[OK] Generated structured transcript saved to: {transcript_path}")
        return transcript_path
        
    except Exception as e:
        print(f"[ERROR] Error generating structured transcript: {e}")
        return None

def generate_transcript(topic="History", model=ModelCategories.getWriteTranscriptModel(), word_count=1000, skip_research=False):
    """
    Generate a complete transcript
    
    Args:
        topic: The main topic to focus on
        model: The OpenAI model to use
        word_count: The desired word count for the transcript (default: 1000)
        skip_research: If True, skip finding relevant research
        
    Returns:
        Path to the generated transcript file
    """
    try:
        print(f"[INFO] Generating transcript for topic: {topic} with {word_count} words")
        
        # Create output directory if it doesn't exist
        output_dir = "Transcript"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        filename = f"ww2_{topic.lower().replace(' ', '_')}_transcript.txt"
        transcript_path = os.path.join(output_dir, filename)
        
        # Find relevant research if not skipped
        relevant_research = ""
        if not skip_research:
            print("[INFO] Finding relevant research...")
            relevant_research = find_relevant_research(topic)
        else:
            print("[INFO] Skipping research as requested")
        
        # Generate the complete transcript
        print("[INFO] Generating complete transcript...")
        transcript = generate_complete_transcript(topic, relevant_research, model=model, word_count=word_count)
        
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
    parser.add_argument("--word-count", type=int, default=1000, help="Desired word count for the transcript")
    parser.add_argument("--structured", action="store_true", help="Generate a structured essay with intro, body, conclusion")
    parser.add_argument("--subtopics", type=str, nargs="+", help="Subtopics for body paragraphs (use with --structured)")
    parser.add_argument("--num-subtopics", type=int, default=3, help="Number of subtopics to auto-generate if --subtopics is not provided")
    parser.add_argument("--skip-research", action="store_true", help="Skip finding relevant research")
    
    args = parser.parse_args()
    
    # Generate the transcript
    if args.structured:
        transcript_file = generate_structured_transcript(args.topic, args.subtopics, args.model, args.num_subtopics, args.skip_research)
    else:
        transcript_file = generate_transcript(args.topic, args.model, args.word_count, args.skip_research)
    
    if transcript_file:
        print(f"[OK] Successfully generated transcript: {transcript_file}")
    else:
        print("[ERROR] Failed to generate transcript")

if __name__ == "__main__":
    main()

