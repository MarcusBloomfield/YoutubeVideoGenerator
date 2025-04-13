import os
import datetime

# Import project modules for the video generation steps
import VideoTranscriptGenerator
import CreateNarration
import GenerateScenes
import Combine
import CleanupProject
import OpenAiQuerying
import TranscriptSeperator
from Models import ModelCategories

def read_topics_file():
    """Read existing topics from Topics.txt file"""
    topics = []
    if os.path.exists("Topics.txt"):
        with open("Topics.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    topics.append(line)
    return topics

def save_topic(theme, topic):
    """Save a generated topic to the Topics.txt file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create directory if it doesn't exist
    if not os.path.exists("Topics.txt"):
        with open("Topics.txt", "w", encoding="utf-8") as f:
            f.write("# Generated Topics for YouTube Video Generator\n\n")
    
    # Append the new topic
    with open("Topics.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {theme}: {topic}\n")

def generate_topic_idea(theme, log_message=None, model=None):
    """
    Generate a specific video topic idea based on a broader theme.
    
    Args:
        theme: The general theme or category (e.g., "World War II", "Space Exploration")
        log_message: Function to log messages (optional)
        model: The OpenAI model to use (optional)
        
    Returns:
        str: A specific topic idea for video generation
    """
    # Set up logging if not provided
    if log_message is None:
        log_message = lambda msg, level='info': print(f"[{level.upper()}] {msg}")
    
    log_message(f"Generating topic idea for theme: {theme}", 'info')
    
    # Read existing topics to avoid duplicates
    existing_topics = read_topics_file()
    if existing_topics:
        log_message(f"Found {len(existing_topics)} existing topics in Topics.txt", 'info')
    
    # Create a prompt for OpenAI that includes previous topics to avoid
    if existing_topics:
        # Extract just the topic names from the last 10 entries
        recent_topics = []
        for line in existing_topics[-10:]:
            if ":" in line:
                topic_part = line.split(":", 1)[1].strip()
                recent_topics.append(topic_part)
        
        if recent_topics:
            topics_to_avoid = ", ".join([f'"{t}"' for t in recent_topics])
            prompt = f"""Generate a specific, engaging video topic related to "{theme}".
Return ONLY the topic title (1-4 words), without quotes or additional text or any other type of formatting.

IMPORTANT: Do NOT generate any of these previously used topics: {topics_to_avoid}"""
        else:
            prompt = f"""Generate a specific, engaging video topic related to "{theme}".
Return ONLY the topic title (1-4 words), without quotes or additional text or any other type of formatting."""
    else:
        prompt = f"""Generate a specific, engaging video topic related to "{theme}".
Return ONLY the topic title (1-4 words), without quotes or additional text or any other type of formatting."""
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        log_message("Error: OpenAI API key not set", 'error')
        return None
    
    # Query OpenAI for a topic idea
    try:
        # Use a more concise model for this simple task or use the provided one
        if model is None:
            model = ModelCategories.getDefaultModel()
            
        log_message(f"Using model: {model} for topic generation", 'info')
        topic_idea = OpenAiQuerying.query_openai(prompt, model=model)
        
        if not topic_idea:
            log_message("Failed to generate topic idea", 'error')
            return None
        
        # Clean up the response
        topic_idea = topic_idea.strip()
        log_message(f"Generated topic idea: {topic_idea}", 'info')
        
        # Save to file
        save_topic(theme, topic_idea)
        log_message("Topic saved to Topics.txt", 'info')
        
        return topic_idea
        
    except Exception as e:
        log_message(f"Error generating topic idea: {str(e)}", 'error')
        return None

def generate_and_create_video(theme, word_count=1000, output_name=None, log_message=None, update_progress=None, model=None):
    """
    Generate a topic based on a theme and then create a full video.
    
    Args:
        theme: The general theme to generate a topic from
        word_count: The desired word count for the transcript
        output_name: Optional name for the output video file
        log_message: Function to log messages
        update_progress: Function to update progress
        model: The OpenAI model to use for topic generation
        
    Returns:
        tuple: (success, message, topic) - success is a boolean indicating if the operation was successful,
               message contains information about the operation, topic is the generated topic
    """
    # Set up logging if not provided
    if log_message is None:
        log_message = lambda msg, level='info': print(f"[{level.upper()}] {msg}")
    
    if update_progress is None:
        update_progress = lambda percent, message=None: print(f"Progress: {percent}% - {message or ''}")
    
    # Generate a topic idea
    log_message(f"Generating video topic based on theme: {theme}", 'info')
    update_progress(5, "Generating topic idea...")
    
    topic = generate_topic_idea(theme, log_message, model)
    
    if not topic:
        log_message("Failed to generate a topic. Cannot proceed.", 'error')
        return False, "Failed to generate a topic", None
    
    log_message(f"Starting video generation for generated topic: {topic}", 'info')
    update_progress(10, f"Topic generated: {topic}")
    
    # Generate the full video with the topic
    result = generate_full_video(
        topic=topic,
        word_count=word_count,
        output_name=output_name,
        log_message=log_message,
        update_progress=update_progress
    )
    
    return True, result, topic

def generate_full_video(topic, word_count=1000, output_name=None, log_message=None, update_progress=None, capture_stdout=None, generate_transcript=None, create_narration=None, generate_scenes=None, combine_media=None, cleanup_project=None, separate_transcript=None, parse_transcripts_to_csv=None, match_audio_to_transcript=None, set_transcript_csv_length=None):
    """Generate a full video by executing all steps in sequence:
    1. Clean up project folders
    2. Generate transcript
    3. Seperate transcript into scenes
    4. Create narration
    5. Parse transcripts to CSV
    6. Match audio to transcript in CSV
    7. Set transcript CSV length
    8. Generate scenes
    9. Combine media
    10. Clean up project folders
    
    Args:
        topic: The main topic for the video
        word_count: The desired word count for the transcript
        output_name: Optional name for the output video file
        log_message: Function to log messages
        update_progress: Function to update progress
        capture_stdout: Function to capture stdout
        generate_transcript: Function to generate transcript
        separate_transcript: Function to separate transcript into scenes
        create_narration: Function to create narration
        parse_transcripts_to_csv: Function to parse transcripts to CSV
        match_audio_to_transcript: Function to match audio to transcript in CSV
        set_transcript_csv_length: Function to set transcript CSV length
        generate_scenes: Function to generate scenes
        combine_media: Function to combine media
        cleanup_project: Function to clean up project
    
    Returns:
        A summary of the operations performed
    """
    # Check if we're running standalone or through the GUI
    # If running standalone, define dummy functions for GUI-specific functions
    if log_message is None:
        log_message = lambda msg, level='info': print(f"[{level.upper()}] {msg}")
    
    if update_progress is None:
        update_progress = lambda percent, message=None: print(f"Progress: {percent}% - {message or ''}")
        
    if capture_stdout is None:
        # Simple version of capture_stdout for standalone use
        def simple_capture(func, *args, **kwargs):
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                result = func(*args, **kwargs)
            return f.getvalue()
        capture_stdout = simple_capture
    
    # If function references are not provided, use direct module functions
    if cleanup_project is None:
        # Default cleanup function preserves output files
        cleanup_project = lambda: CleanupProject.clean_project(preserve_output=True)
    
    if generate_transcript is None:
        generate_transcript = lambda topic, word_count: VideoTranscriptGenerator.generate_transcript(topic=topic, word_count=word_count)
    
    if separate_transcript is None:
        separate_transcript = TranscriptSeperator.process_all_transcripts
    
    if create_narration is None:
        def simple_create_narration():
            narration_creator = CreateNarration.CreateNarration()
            return narration_creator.process_transcripts()
        create_narration = simple_create_narration
    
    if parse_transcripts_to_csv is None:
        import ParseTranscriptsToCsv
        parse_transcripts_to_csv = ParseTranscriptsToCsv.main
    
    if match_audio_to_transcript is None:
        import MatchAudioToTranscriptInCsv
        match_audio_to_transcript = MatchAudioToTranscriptInCsv.match_audio_to_transcript
    
    if set_transcript_csv_length is None:
        import SetTranscriptCsvLength
        def set_csv_length():
            csv_file_path = "transcripts_data.csv"
            return SetTranscriptCsvLength.update_csv_with_audio_lengths(csv_file_path)
        set_transcript_csv_length = set_csv_length
    
    if generate_scenes is None:
        def simple_generate_scenes():
            scene_generator = GenerateScenes.GenerateScenes()
            return scene_generator.main()
        generate_scenes = simple_generate_scenes
    
    if combine_media is None:
        def simple_combine_media(output_name):
            combiner = Combine.Combine()
            return combiner.main(output_name)
        combine_media = simple_combine_media
    
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        log_message("Error: OpenAI API key not set", 'error')
        return "Error: OpenAI API key not set. Please set it in the Settings tab."
    
    # If no output name is provided, create one based on the topic
    if not output_name:
        # Convert topic to a suitable filename: lowercase, spaces to underscores, add date
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        output_name = f"video_{topic.lower().replace(' ', '_')}_{timestamp}"
        log_message(f"Generated output filename: {output_name}", 'info')
    
    log_message(f"Starting full video generation for topic: {topic}", 'info')
    results = []
    
    try:
        # Step 1: Run cleanup to start with fresh folders
        log_message("Step 1/10: Cleaning up project folders before starting...", 'info')
        update_progress(5, "Cleaning up project folders...")
        def initial_cleanup():
            return CleanupProject.clean_project(preserve_output=True)
        initial_cleanup_result = capture_stdout(initial_cleanup)
        results.append(f"INITIAL PROJECT CLEANUP:\n{initial_cleanup_result}")
        
        # Step 2: Generate transcript
        log_message("Step 2/10: Generating transcript...", 'info')
        update_progress(15, "Generating transcript...")
        transcript_result = capture_stdout(lambda: generate_transcript(topic, word_count))
        results.append(f"TRANSCRIPT GENERATION:\n{transcript_result}")
        
        # Step 3: Separate transcript into scenes
        log_message("Step 3/10: Separating transcript into scenes...", 'info')
        update_progress(25, "Separating transcript...")
        separate_result = capture_stdout(separate_transcript)
        results.append(f"TRANSCRIPT SEPARATION:\n{separate_result}")
        
        # Step 4: Create narration
        log_message("Step 4/10: Creating narration...", 'info')
        update_progress(35, "Creating narration...")
        narration_result = capture_stdout(create_narration)
        results.append(f"NARRATION CREATION:\n{narration_result}")
        
        # Step 5: Parse transcripts to CSV
        log_message("Step 5/10: Parsing transcripts to CSV...", 'info')
        update_progress(45, "Parsing transcripts to CSV...")
        parse_result = capture_stdout(parse_transcripts_to_csv)
        results.append(f"PARSING TRANSCRIPTS TO CSV:\n{parse_result}")
        
        # Step 6: Match audio to transcript in CSV
        log_message("Step 6/10: Matching audio to transcript in CSV...", 'info')
        update_progress(55, "Matching audio to transcript...")
        match_result = capture_stdout(match_audio_to_transcript)
        results.append(f"MATCHING AUDIO TO TRANSCRIPT:\n{match_result}")
        
        # Step 7: Set transcript CSV length
        log_message("Step 7/10: Setting transcript CSV length...", 'info')
        update_progress(65, "Setting transcript CSV length...")
        set_length_result = capture_stdout(set_transcript_csv_length)
        results.append(f"SETTING TRANSCRIPT CSV LENGTH:\n{set_length_result}")
        
        # Step 8: Generate scenes
        log_message("Step 8/10: Generating scenes...", 'info')
        update_progress(75, "Generating scenes...")
        scenes_result = capture_stdout(generate_scenes)
        results.append(f"SCENE GENERATION:\n{scenes_result}")
        
        # Step 9: Combine media
        log_message("Step 9/10: Combining media...", 'info')
        update_progress(85, "Combining media...")
        combine_result = capture_stdout(lambda: combine_media(output_name))
        results.append(f"MEDIA COMBINATION:\n{combine_result}")
        
        # Step 10: Clean up project
        log_message("Step 10/10: Final cleanup of project folders...", 'info')
        update_progress(95, "Final cleanup of project folders...")
        # Use a special cleanup function that preserves the output video we just created
        def final_cleanup():
            return CleanupProject.clean_project(preserve_output=True)
        cleanup_result = capture_stdout(final_cleanup)
        results.append(f"FINAL PROJECT CLEANUP:\n{cleanup_result}")
        
        # Process complete
        update_progress(100, "Full video generation complete!")
        log_message(f"Full video generation completed successfully. Output file: {output_name}", 'info')
        
        return "\n\n====================\n\n".join(results)
    except Exception as e:
        error_msg = f"Error during full video generation: {str(e)}"
        log_message(error_msg, 'error')
        return error_msg

def main():
    """Run the full video generation process from the command line
    
    Usage examples:
    
    1. Generate a video with a specific topic:
       python GenerateFullVideo.py --topic "D-Day Normandy Invasion" --word-count 1500
    
    2. Generate a topic from a theme, then create a video:
       python GenerateFullVideo.py --theme "World War II" --word-count 1200
    
    3. Only generate a topic idea without creating a video:
       python GenerateFullVideo.py --theme "Ancient Rome" --topic-only
    
    4. Generate a topic using a specific model:
       python GenerateFullVideo.py --theme "Space Exploration" --topic-only --model "gpt-4o"
    
    5. Generate a video with custom output name:
       python GenerateFullVideo.py --theme "Renaissance Art" --output-name "renaissance_video"
       
    6. List previously generated topics:
       python GenerateFullVideo.py --list-topics
    """
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables (for API key)
    load_dotenv()
    
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Generate a complete video from transcript to final output")
    
    # Create a group for the two mutually exclusive options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic", type=str, help="Main topic for the video")
    group.add_argument("--theme", type=str, help="Theme to generate a topic from")
    group.add_argument("--list-topics", action="store_true", help="List all previously generated topics")
    
    # Add a flag to only generate a topic without creating a video
    parser.add_argument("--topic-only", action="store_true", help="Only generate a topic without creating a video")
    parser.add_argument("--word-count", type=int, default=1000, help="Desired word count for the transcript")
    parser.add_argument("--output-name", type=str, help="Output filename (optional)")
    parser.add_argument("--model", type=str, help="OpenAI model to use (optional, uses default if not specified)")
    
    args = parser.parse_args()
    
    # List previously generated topics
    if args.list_topics:
        topics = read_topics_file()
        if topics:
            print("\nPreviously generated topics:")
            for i, line in enumerate(topics, 1):
                print(f"{i}. {line}")
            print(f"\nTotal: {len(topics)} topics")
        else:
            print("No topics found in Topics.txt")
        return
    
    if args.theme:
        if args.topic_only:
            # Only generate a topic from the theme without creating a video
            print(f"Generating topic idea for theme: {args.theme}")
            topic = generate_topic_idea(args.theme, model=args.model)
            
            if topic:
                print(f"\nGenerated topic: {topic}")
            else:
                print("Error: Failed to generate a topic.")
        else:
            # Generate a topic from the theme and create a video
            print(f"Generating video from theme: {args.theme}")
            success, result, topic = generate_and_create_video(
                theme=args.theme,
                word_count=args.word_count,
                output_name=args.output_name,
                model=args.model
            )
            if success:
                print(f"\nGenerated topic: {topic}\n")
                print(result)
            else:
                print(f"Error: {result}")
    elif args.topic:
        if args.topic_only:
            print("Warning: --topic-only flag is ignored when using --topic")
            
        # Generate the full video with the provided topic
        print(f"Generating video with topic: {args.topic}")
        result = generate_full_video(
            topic=args.topic,
            word_count=args.word_count,
            output_name=args.output_name
        )
        print(result)

if __name__ == "__main__":
    main() 