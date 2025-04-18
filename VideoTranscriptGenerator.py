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


def save_transcript(transcript_text, topic, structured=False, output_dir="Transcript"):
    """
    Saves a transcript to a file
    
    Args:
        transcript_text: The transcript content to save
        topic: The main topic (used for filename generation)
        structured: Whether this is a structured transcript (affects filename)
        output_dir: Directory to save the transcript in
        
    Returns:
        Path to the saved transcript file
    """
    try:

        if transcript_text == None or transcript_text == "":
            print("[ERROR] Transcript text is empty")
            return None

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Sanitize topic for filename - remove invalid characters
        sanitized_topic = topic.lower()
        # Replace invalid filename characters
        for char in [':', '/', '\\', '*', '?', '"', '<', '>', '|']:
            sanitized_topic = sanitized_topic.replace(char, '_')
        sanitized_topic = sanitized_topic.replace(' ', '_')

        # Generate output filename based on transcript type
        type_suffix = "structured_transcript" if structured else "transcript"
        filename = f"ww2_{sanitized_topic}_{type_suffix}.txt"
        transcript_path = os.path.join(output_dir, filename)
        
        # Write to file
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        # Estimate actual word count for logging
        actual_word_count = len(transcript_text.split())
        
        # Log appropriate message based on transcript type
        if structured:
            print(f"[OK] Generated structured transcript with approximately {actual_word_count} words saved to: {transcript_path}")
        else:
            print(f"[OK] Generated transcript saved to: {transcript_path}")
            
        return transcript_path
        
    except Exception as e:
        print(f"[ERROR] Error saving transcript: {e}")
        return None

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
        # Ensure minimum word count
        MINIMUM_WORD_COUNT = 100
        if word_count < MINIMUM_WORD_COUNT:
            print(f"[WARNING] Word count {word_count} is too low. Using minimum of {MINIMUM_WORD_COUNT} words.")
            word_count = MINIMUM_WORD_COUNT
            
        print(f"[INFO] Generating transcript with {word_count} words")
        
        # Create a more detailed prompt that works better for short transcripts
        prompt = f"""
        Create a complete, detailed transcript for a video about {topic} during World War II.

        IMPORTANT REQUIREMENTS:
        - Dramatise the events
        - Make it interesting
        - Make it engaging
        - For A youtube short video
        - NO INTRO OR CONCLUSION
        - Total length: Approximately {word_count} words
        - Content should be historically accurate with dates, names, and specific details
        - Events must be presented in chronological order
        - Format: Continuous paragraphs optimized for narration
        - NO section headers or formatting
        - NO chapter headings or any other text blocks
        - The transcript should flow as one continuous piece of text
        
        Relevant research to incorporate: {relevant_research}
        
        Generate ONLY plain text with NO headings, NO formatting, and NO additional text blocks.
        """
        
        # Query OpenAI to generate the complete transcript
        transcript_text = query_openai(prompt, model=model)
        
        if not transcript_text:
            print("[ERROR] No response from OpenAI API for transcript generation")
            return ""
            
        # Check if result is empty or too short, and retry with a simpler prompt if needed
        if len(transcript_text.strip()) < 20:  # Arbitrary threshold for "too short"
            print("[WARNING] Generated transcript is too short. Retrying with simpler prompt...")
            
            simpler_prompt = f"""
            Write a short narrative about {topic} during World War II in approximately {word_count} words.
            Include specific historical details and present information chronologically.
            Format as a continuous paragraph with no headings or special formatting.
            """
            
            transcript_text = query_openai(simpler_prompt, model=model)
            
        return transcript_text
        
    except Exception as e:
        print(f"[ERROR] Error generating transcript: {e}")
        return ""

def generate_subtopics(topic, num_subtopics=3, model=ModelCategories.getDefaultModel(), total_word_count=3000):
    """
    Generate subtopics for a structured video essay based on the main topic
    
    Args:
        topic: The main topic to generate subtopics for
        num_subtopics: Number of subtopics to generate (default: 3, but may be overridden by AI)
        model: The OpenAI model to use
        total_word_count: Total target word count for the transcript (used to determine optimal number of subtopics)
        
    Returns:
        List of generated subtopics
    """
    try:
        # For very low word counts, limit the number of subtopics regardless of input
        if total_word_count < 500:
            # Force a smaller number of subtopics for very short transcripts
            requested_subtopics = min(2, num_subtopics)
            print(f"[INFO] Low word count ({total_word_count}), limiting to {requested_subtopics} subtopics")
        else:
            requested_subtopics = num_subtopics
            
        print(f"[INFO] Determining appropriate number of subtopics for topic: {topic} with target {total_word_count} words")
        
        prompt = f"""
        Determine the optimal number of subtopics and generate them for a video essay about {topic} during World War II.
        
        The total transcript will be approximately {total_word_count} words in length.
        
        Requirements:
        - YOU decide the appropriate number of subtopics based on the topic's breadth and the total word count
        - For this {total_word_count} word transcript, suggest no more than {requested_subtopics} subtopics
        - For shorter content (under 5,000 words), use fewer subtopics (2-3)
        - Each subtopic should cover a significant aspect of {topic}
        - Subtopics MUST be arranged in strict chronological order of events
        - Subtopics should be distinct from each other
        - Subtopics should be specific, not general
        - Format: Return ONLY a numbered list with no additional text
        - Each subtopic should be 3-5 words
        
        Example format:
        1. Early War Preparations
        2. Major Battlefield Confrontations
        3. Post-War Consequences
        """
        
        # Query OpenAI to generate subtopics
        response = query_openai(prompt, model=model)
        
        if not response:
            print("[ERROR] No response from OpenAI API for subtopic generation")
            return ["Key Historical Events"]  # Return at least one default subtopic
        
        # Parse the numbered list
        subtopics = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 20)):
                # Remove the number and any leading/trailing whitespace
                subtopic = line.split('.', 1)[1].strip()
                subtopics.append(subtopic)
        
        # Ensure we have at least one subtopic
        if not subtopics:
            print("[WARNING] Failed to parse subtopics from response. Using default subtopic.")
            subtopics = ["Key Historical Events"]
            
        print(f"[OK] Generated {len(subtopics)} subtopics in chronological order: {', '.join(subtopics)}")
        return subtopics
        
    except Exception as e:
        print(f"[ERROR] Error generating subtopics: {e}")
        return ["Key Historical Events"]  # Return at least one default subtopic

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

def generate_structured_transcript(topic, subtopics=None, model=ModelCategories.getWriteTranscriptModel(), num_subtopics=3, skip_research=False, total_word_count=3000):
    """
    Generate a structured transcript with intro, body paragraphs, and conclusion using a single prompt approach
    
    Args:
        topic: The main topic to focus on
        subtopics: List of subtopics for body paragraphs (if None, will auto-generate)
        model: The OpenAI model to use
        num_subtopics: Number of subtopics to auto-generate if subtopics is None (may be overridden by AI)
        skip_research: If True, skip finding relevant research
        total_word_count: Total target word count for the transcript (default: 3000)
        
    Returns:
        Path to the generated transcript file
    """
    try:
        # Ensure minimum word count to prevent empty transcripts
        MINIMUM_WORD_COUNT = 250
        if total_word_count < MINIMUM_WORD_COUNT:
            print(f"[WARNING] Word count {total_word_count} is too low for structured transcript. Using minimum of {MINIMUM_WORD_COUNT} words.")
            total_word_count = MINIMUM_WORD_COUNT
            
        print(f"[INFO] Generating structured transcript for topic: {topic} with target {total_word_count} words")
        
        # Find relevant research if not skipped
        relevant_research = ""
        if not skip_research:
            print("[INFO] Finding relevant research...")
            relevant_research = find_relevant_research(topic)
        else:
            print("[INFO] Skipping research as requested")
        
        # Auto-generate subtopics if not provided
        if not subtopics:
            # For very short transcripts, reduce the number of subtopics
            if total_word_count < 500:
                adjusted_num_subtopics = 2
                print(f"[INFO] Reducing subtopics to {adjusted_num_subtopics} due to low word count")
            else:
                adjusted_num_subtopics = num_subtopics
                
            print(f"[INFO] Auto-generating subtopics for {total_word_count} words...")
            subtopics = generate_subtopics(topic, adjusted_num_subtopics, model, total_word_count)
            if not subtopics:
                print("[WARNING] Failed to generate subtopics. Proceeding with generic subtopics.")
                
                # Adjust number of generic subtopics based on word count
                if total_word_count < 500:
                    subtopics = ["Historical Background", "Key Events"]
                elif total_word_count < 1000:
                    subtopics = ["Historical Background", "Key Events", "Outcomes"]
                else:
                    subtopics = ["Historical Background", "Early Developments", "Key Events", "Critical Turning Points", "Final Outcomes"]
                    if total_word_count > 5000:
                        # Add more generic subtopics for longer transcripts
                        additional = ["Military Strategies", "Key Figures", "Civilian Impact", "Political Consequences", 
                                     "International Reactions", "Technological Developments", "Aftermath Effects", 
                                     "Historical Significance", "Long-term Influence", "Legacy"]
                        # Scale the number of additional subtopics based on word count
                        additional_count = min(len(additional), max(1, total_word_count // 5000))
                        subtopics.extend(additional[:additional_count])
        
        # Maximum tokens that can be handled in a single API call
        # Different models have different token limits
        # For most models, a 10,000 word transcript would be around 13,000-15,000 tokens
        max_words_per_call = 7500
        
        # Check if we can generate the entire transcript in one go
        if total_word_count <= max_words_per_call:
            print(f"[INFO] Generating entire {total_word_count} word transcript in a single API call")
            
            # Single prompt approach for complete transcript
            subtopics_text = ", ".join(subtopics)
            
            # Create formatted topics list for the prompt
            topics_list = "\n".join([f"{i+1}. {subtopic}" for i, subtopic in enumerate(subtopics)])
            
            full_prompt = f"""
            Create a complete, detailed transcript for a video about {topic} during World War II.

            IMPORTANT REQUIREMENTS:
            - Total length: Approximately {total_word_count} words
            - Content should be historically accurate with dates, names, and specific details
            - Events must be presented in strict chronological order
            - NO formatting whatsoever - pure text only
            - NO chapter headings, section headers, or any other text blocks
            - The transcript should flow as one continuous piece of text
            
            The transcript should cover the following topics IN THIS EXACT ORDER (they are already arranged chronologically):
            
            {topics_list}
            
            Structure:
            1. Start with an introduction
            2. Cover each topic in order, with smooth transitions between topics
            3. End with a conclusion
            
            Relevant research to incorporate: {relevant_research}
            
            Generate ONLY plain text with NO headings, NO formatting, and NO additional text blocks.
            """
            
            # Generate the complete transcript in one call
            print("[INFO] Requesting transcript generation...")
            full_transcript = query_openai(full_prompt, model=model)
            
        else:
            print(f"[INFO] Transcript length ({total_word_count} words) exceeds maximum for single API call")
            print(f"[INFO] Generating transcript in multiple chunks with efficient distribution")
            
            # Use an approach with fewer, larger chunks
            full_transcript = ""
            
            # Structure: Intro (5%) + Body chunks (90%) + Conclusion (5%)
            # For very short transcripts, ensure minimums
            min_section_words = 30  # Minimum words per section
            
            intro_word_count = max(min_section_words, int(total_word_count * 0.05))
            conclusion_word_count = max(min_section_words, int(total_word_count * 0.05))
            
            # Adjust if intro + conclusion would exceed total
            if intro_word_count + conclusion_word_count > total_word_count * 0.4:
                # Cap at 40% of total
                ratio = total_word_count * 0.4 / (intro_word_count + conclusion_word_count)
                intro_word_count = int(intro_word_count * ratio)
                conclusion_word_count = int(conclusion_word_count * ratio)
            
            body_total_word_count = total_word_count - intro_word_count - conclusion_word_count
            
            # Calculate estimated words per subtopic, ensuring a minimum
            min_subtopic_words = 50
            words_per_subtopic = max(min_subtopic_words, body_total_word_count // len(subtopics))
            
            # Generate intro and first subtopic together if possible
            first_chunk_size = min(intro_word_count + words_per_subtopic, max_words_per_call)
            first_subtopic_words = first_chunk_size - intro_word_count
            
            print(f"[INFO] Generating introduction and first subtopic ({first_chunk_size} words)")
            
            first_chunk_prompt = f"""
            Create the beginning portion of a transcript for a video about {topic} during World War II.
            
            This first portion should include:
            1. An introduction: Set historical context and introduce the key themes
            2. Content about: {subtopics[0]}
            
            IMPORTANT REQUIREMENTS:
            - Total length for this portion: Approximately {first_chunk_size} words
            - Content should be historically accurate with dates, names, and specific details
            - Events must be presented in strict chronological order
            - NO formatting whatsoever - pure text only
            - DO NOT include any headings or titles
            - The text should flow as one continuous piece
            
            Relevant research to incorporate: {relevant_research}
            
            Generate ONLY plain text with NO headings, NO formatting, and NO additional text blocks.
            """
            
            # Generate the first chunk (intro + first subtopic)
            first_chunk = query_openai(first_chunk_prompt, model=model)
            full_transcript += first_chunk + "\n\n"
            
            # Keep track of remaining subtopics and words
            remaining_subtopics = subtopics[1:]
            remaining_body_words = body_total_word_count - first_subtopic_words
            
            # If no remaining subtopics, skip to conclusion
            if remaining_subtopics:
                # Calculate words per remaining subtopic, ensuring minimum
                words_per_remaining_subtopic = max(min_subtopic_words, 
                                                 remaining_body_words // max(1, len(remaining_subtopics)))
                
                # Generate middle chunks (remaining body content)
                subtopics_per_chunk = max(1, max_words_per_call // words_per_remaining_subtopic)
                
                while remaining_subtopics:
                    # Take a batch of subtopics for this chunk
                    batch_subtopics = remaining_subtopics[:subtopics_per_chunk]
                    remaining_subtopics = remaining_subtopics[subtopics_per_chunk:]
                    
                    # Calculate word count for this chunk
                    batch_word_count = min(words_per_remaining_subtopic * len(batch_subtopics), max_words_per_call)
                    
                    subtopics_text = ", ".join(batch_subtopics)
                    print(f"[INFO] Generating content for topics: {subtopics_text} ({batch_word_count} words)")
                    
                    # Content from previous chunk to ensure coherence
                    previous_context = full_transcript[-500:] if full_transcript else ""
                    
                    # Create topics to cover in this batch
                    topics_to_cover = "\n".join([f"- {subtopic}" for subtopic in batch_subtopics])
                    
                    middle_chunk_prompt = f"""
                    Continue the transcript for a video about {topic} during World War II.
                    
                    Previous content ends with: "{previous_context}"
                    
                    Now cover the following topics IN THIS EXACT ORDER (they are already arranged chronologically):
                    
                    {topics_to_cover}
                    
                    IMPORTANT REQUIREMENTS:
                    - Total length for this portion: Approximately {batch_word_count} words
                    - Content should be historically accurate with dates, names, and specific details
                    - Events must be presented in strict chronological order
                    - NO formatting whatsoever - pure text only
                    - NO headings or titles for each topic
                    - Create smooth transitions between topics
                    - The text should flow as one continuous piece
                    
                    Relevant research to incorporate: {relevant_research}
                    
                    Generate ONLY plain text with NO headings, NO formatting, and NO additional text blocks.
                    """
                    
                    # Generate this chunk
                    middle_chunk = query_openai(middle_chunk_prompt, model=model)
                    full_transcript += middle_chunk + "\n\n"
            
            # Generate conclusion as final chunk
            print(f"[INFO] Generating conclusion ({conclusion_word_count} words)")
            
            # Content from previous chunk to ensure coherence
            previous_context = full_transcript[-500:] if full_transcript else ""
            
            conclusion_prompt = f"""
            Create the conclusion for a video transcript about {topic} during World War II.
            
            Previous content ends with: "{previous_context}"
            
            This conclusion should:
            - Summarize the key points covered throughout the transcript: {', '.join(subtopics)}
            - Discuss the historical significance and long-term impact
            - Provide thought-provoking closing statements
            
            IMPORTANT REQUIREMENTS:
            - Length: Approximately {conclusion_word_count} words
            - NO headings or titles
            - NO formatting whatsoever - pure text only
            - The text should flow naturally from the previous content
            
            Generate ONLY plain text with NO headings, NO formatting, and NO additional text blocks.
            """
            
            # Generate the conclusion
            conclusion = query_openai(conclusion_prompt, model=model)
            full_transcript += conclusion
        
        # Save the transcript using the dedicated function
        return save_transcript(full_transcript, topic, structured=True)
        
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
        
        # Save the transcript using the dedicated function
        return save_transcript(transcript, topic, structured=False)
        
    except Exception as e:
        print(f"[ERROR] Error generating transcript: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate a World War 2 video transcript")
    parser.add_argument("--topic", type=str, default="History", help="Main topic to focus on")
    parser.add_argument("--model", type=str, default=ModelCategories.getWriteTranscriptModel(), help="OpenAI model to use")
    parser.add_argument("--word-count", type=int, default=3000, help="Desired word count for the transcript")
    parser.add_argument("--structured", action="store_true", help="Generate a structured essay with intro, body, conclusion")
    parser.add_argument("--subtopics", type=str, nargs="+", help="Subtopics for body paragraphs (use with --structured)")
    parser.add_argument("--num-subtopics", type=int, default=3, help="Number of subtopics to auto-generate if --subtopics is not provided")
    parser.add_argument("--skip-research", action="store_true", help="Skip finding relevant research")
    
    args = parser.parse_args()
    
    # Generate the transcript
    if args.structured:
        transcript_file = generate_structured_transcript(args.topic, args.subtopics, args.model, args.num_subtopics, args.skip_research, args.word_count)
    else:
        transcript_file = generate_transcript(args.topic, args.model, args.word_count, args.skip_research)
    
    if transcript_file != None and transcript_file != "":
        print(f"[OK] Successfully generated transcript: {transcript_file}")
    else:
        print("[ERROR] Failed to generate transcript")

if __name__ == "__main__":
    main()

