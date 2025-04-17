import os
import datetime
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import project modules for the video generation steps
import VideoTranscriptGenerator
import CreateNarration
import GenerateScenes
import Combine
import MakeYoutubeShort
import CleanupProject
import OpenAiQuerying
import TranscriptSeperator
import ParseTranscriptsToCsv
import MatchAudioToTranscriptInCsv
import SetTranscriptCsvLength
from Models import ModelCategories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log", mode="a")
    ]
)
logger = logging.getLogger(__name__)

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
    
    # Create file if it doesn't exist
    if not os.path.exists("Topics.txt"):
        with open("Topics.txt", "w", encoding="utf-8") as f:
            f.write("# Generated Topics for YouTube Video Generator\n\n")
    
    # Append the new topic
    with open("Topics.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {theme}: {topic}\n")

def generate_topic_idea(theme, model=None):
    """
    Generate a specific video topic idea based on a broader theme.
    
    Args:
        theme: The general theme or category (e.g., "World War II", "Space Exploration")
        model: The OpenAI model to use (optional)
        
    Returns:
        str: A specific topic idea for video generation
    """
    logger.info(f"Generating topic idea for theme: {theme}")
    
    # Read existing topics to avoid duplicates
    existing_topics = read_topics_file()
    if existing_topics:
        logger.info(f"Found {len(existing_topics)} existing topics in Topics.txt")
    
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
        logger.error("OpenAI API key not set")
        return None
    
    # Query OpenAI for a topic idea
    try:
        # Use a more concise model for this simple task or use the provided one
        if model is None:
            model = ModelCategories.getDefaultModel()
            
        logger.info(f"Using model: {model} for topic generation")
        topic_idea = OpenAiQuerying.query_openai(prompt, model=model)
        
        if not topic_idea:
            logger.error("Failed to generate topic idea")
            return None
        
        # Clean up the response
        topic_idea = topic_idea.strip()
        logger.info(f"Generated topic idea: {topic_idea}")
        
        # Save to file
        save_topic(theme, topic_idea)
        logger.info("Topic saved to Topics.txt")
        
        return topic_idea
        
    except Exception as e:
        logger.error(f"Error generating topic idea: {str(e)}")
        return None

def verify_file_exists(filepath, min_size=0, error_msg=None):
    """Verify that a file exists and optionally has a minimum size"""
    if not os.path.exists(filepath):
        if error_msg:
            logger.error(error_msg)
        else:
            logger.error(f"File not found: {filepath}")
        return False
    
    if min_size > 0:
        file_size = os.path.getsize(filepath)
        if file_size < min_size:
            logger.error(f"File {filepath} is too small: {file_size} bytes (minimum expected: {min_size})")
            return False
    
    return True

def generate_full_video(
    topic, 
    word_count=1000, 
    output_name=None, 
    youtube_short=False, 
    structured=False, 
    num_subtopics=3, 
    skip_research=False
):
    """
    Generate a full video by executing all steps in sequence
    
    Args:
        topic: The main topic for the video
        word_count: The desired word count for the transcript
        output_name: Optional name for the output video file
        youtube_short: Whether to create a YouTube Short instead of regular video
        structured: Whether to create a structured essay transcript
        num_subtopics: Number of subtopics to auto-generate for structured transcripts
        skip_research: Whether to skip finding research for transcript
    
    Returns:
        str: success or error message
    """
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        return "Error: OpenAI API key not set. Please set it in your environment variables or .env file."
    
    # If no output name is provided, create one based on the topic
    if not output_name:
        # Convert topic to a suitable filename: lowercase, spaces to underscores, add date
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        if youtube_short:
            output_name = f"short_{topic.lower().replace(' ', '_')}_{timestamp}"
        else:
            output_name = f"video_{topic.lower().replace(' ', '_')}_{timestamp}"
        logger.info(f"Generated output filename: {output_name}")
    
    if structured:
        logger.info(f"Starting {'YouTube Short' if youtube_short else 'full video'} generation with structured essay format for topic: {topic}")
    else:
        logger.info(f"Starting {'YouTube Short' if youtube_short else 'full video'} generation for topic: {topic}")
    
    try:
        # Step 1: Run cleanup to start with fresh folders
        logger.info("Step 1/10: Cleaning up project folders before starting...")
        CleanupProject.clean_project(preserve_output=True)
        
        # Step 2: Generate transcript
        logger.info(f"Step 2/10: Generating {'structured' if structured else 'standard'} transcript...")
        
        if structured:
            transcript_file = VideoTranscriptGenerator.generate_structured_transcript(
                topic=topic, 
                subtopics=None, 
                model=ModelCategories.getWriteTranscriptModel(), 
                num_subtopics=num_subtopics,
                skip_research=skip_research,
                total_word_count=word_count
            )
        else:
            transcript_file = VideoTranscriptGenerator.generate_transcript(
                topic=topic, 
                model=ModelCategories.getWriteTranscriptModel(),
                word_count=word_count,
                skip_research=skip_research
            )
        
        # Verify transcript generation
        if not transcript_file:
            return "Error: Failed to generate transcript. Check pipeline.log for details."
        
        if not verify_file_exists(transcript_file, min_size=20, 
                                error_msg=f"Transcript file not created or empty: {transcript_file}"):
            return f"Error: Transcript generation failed. File not found or empty: {transcript_file}"
            
        logger.info(f"Transcript successfully generated: {transcript_file}")
        
        # Step 3: Separate transcript into scenes
        logger.info("Step 3/10: Separating transcript into scenes...")
        TranscriptSeperator.process_all_transcripts()
        
        # Step 4: Create narration
        logger.info("Step 4/10: Creating narration...")
        narration_creator = CreateNarration.CreateNarration()
        narration_creator.process_transcripts()
        
        # Verify audio files were created
        audio_dir = "Audio"
        if not os.path.exists(audio_dir) or not os.listdir(audio_dir):
            return "Error: No audio files were created. Narration step failed."
        
        # Step 5: Parse transcripts to CSV
        logger.info("Step 5/10: Parsing transcripts to CSV...")
        ParseTranscriptsToCsv.main()
        
        # Verify transcripts CSV was created
        csv_file = "transcripts_data.csv"
        if not verify_file_exists(csv_file, min_size=5, 
                                error_msg=f"CSV file not created or empty: {csv_file}"):
            return f"Error: Failed to create transcripts CSV file."
        
        # Step 6: Match audio to transcript in CSV
        logger.info("Step 6/10: Matching audio to transcript in CSV...")
        MatchAudioToTranscriptInCsv.match_audio_to_transcript()
        
        # Step 7: Set transcript CSV length
        logger.info("Step 7/10: Setting transcript CSV length...")
        SetTranscriptCsvLength.update_csv_with_audio_lengths(csv_file)
        
        # Verify CSV has been updated with lengths
        if not verify_file_exists(csv_file, min_size=10, 
                                error_msg=f"CSV file not updated or corrupted: {csv_file}"):
            return f"Error: Failed to update CSV with audio lengths."
        
        # Step 8: Generate scenes
        logger.info("Step 8/10: Generating scenes...")
        scene_generator = GenerateScenes.GenerateScenes()
        scene_generator.main()
        
        # Verify scenes were created
        scenes_dir = "Scenes"
        if not os.path.exists(scenes_dir) or not os.listdir(scenes_dir):
            # This is where things often fail, provide detailed diagnostic info
            logger.error("No scenes were generated in the Scenes directory")
            
            # Check CSV content
            try:
                with open(csv_file, 'r') as f:
                    csv_content = f.read()
                logger.info(f"CSV file contents ({len(csv_content.strip().split(chr(10)))} lines):")
                logger.info(csv_content[:500] + "..." if len(csv_content) > 500 else csv_content)
            except Exception as e:
                logger.error(f"Could not read CSV file: {e}")
            
            # Check audio files
            try:
                audio_files = os.listdir(audio_dir)
                logger.info(f"Audio directory contains {len(audio_files)} files:")
                for file in audio_files[:10]:  # Show first 10 files 
                    logger.info(f"  - {file}")
                if len(audio_files) > 10:
                    logger.info(f"  - ... and {len(audio_files) - 10} more")
            except Exception as e:
                logger.error(f"Could not list audio files: {e}")
                
            return "Error: No scenes were generated. Scene generation failed."
        
        # Step 9: Combine media
        logger.info(f"Step 9/10: {'Creating YouTube Short' if youtube_short else 'Combining media'}...")
        
        if youtube_short:
            shorts_maker = MakeYoutubeShort.MakeYoutubeShort()
            result = shorts_maker.main(output_name)
        else:
            combiner = Combine.Combine()
            result = combiner.main(output_name)
            
        if not result:
            return f"Error: Failed to {'create YouTube Short' if youtube_short else 'combine media'}."
            
        # Step 10: Clean up project except for output
        logger.info("Step 10/10: Final cleanup of project folders...")
        CleanupProject.clean_project(preserve_output=True)
        
        # Video generation completed successfully
        if os.path.isfile(result):
            file_size = os.path.getsize(result) / (1024 * 1024)  # Convert to MB
            logger.info(f"Success! Generated {file_size:.2f}MB {'YouTube Short' if youtube_short else 'video'}: {result}")
            return f"Successfully generated {'YouTube Short' if youtube_short else 'video'}: {result}"
        else:
            return f"Warning: Process completed but output file not found: {result}"
            
    except Exception as e:
        import traceback
        logger.error(f"Error during {'YouTube Short' if youtube_short else 'video'} generation: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Error during {'YouTube Short' if youtube_short else 'video'} generation: {str(e)}"

def generate_and_create_video(
    theme, 
    word_count=1000, 
    output_name=None, 
    model=None, 
    youtube_short=False, 
    structured=False, 
    num_subtopics=3, 
    skip_research=False
):
    """
    Generate a topic based on a theme and then create a full video.
    
    Args:
        theme: The general theme to generate a topic from
        word_count: The desired word count for the transcript
        output_name: Optional name for the output video file
        model: The OpenAI model to use for topic generation
        youtube_short: Whether to create a YouTube Short instead of regular video
        structured: Whether to create a structured essay transcript
        num_subtopics: Number of subtopics to auto-generate for structured transcripts
        skip_research: Whether to skip finding research for transcript
        
    Returns:
        tuple: (success, message, topic) - success is a boolean indicating if the operation was successful,
               message contains information about the operation, topic is the generated topic
    """
    # Generate a topic idea
    logger.info(f"Generating video topic based on theme: {theme}")
    
    topic = generate_topic_idea(theme, model)
    
    if not topic:
        logger.error("Failed to generate a topic. Cannot proceed.")
        return False, "Failed to generate a topic", None
    
    logger.info(f"Starting video generation for generated topic: {topic}")
    
    # Generate the full video with the topic
    result = generate_full_video(
        topic=topic,
        word_count=word_count,
        output_name=output_name,
        youtube_short=youtube_short,
        structured=structured,
        num_subtopics=num_subtopics,
        skip_research=skip_research
    )
    
    # Check if result indicates an error
    is_success = not result.startswith("Error:") and not result.startswith("Warning:")
    return is_success, result, topic

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
       
    7. Create a YouTube Short instead of a regular video:
       python GenerateFullVideo.py --topic "Amazing Facts" --youtube-short
       
    8. Generate a structured essay format transcript:
       python GenerateFullVideo.py --topic "Battle of Stalingrad" --structured --num-subtopics 5
       
    9. Skip research for faster generation (but potentially less accurate content):
       python GenerateFullVideo.py --topic "Battle of Britain" --skip-research
    """
    # Load environment variables (for API key)
    load_dotenv()
    
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Generate a complete video from transcript to final output")
    
    # Create a group for the mutually exclusive options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic", type=str, help="Main topic for the video")
    group.add_argument("--theme", type=str, help="Theme to generate a topic from")
    group.add_argument("--list-topics", action="store_true", help="List all previously generated topics")
    
    # Add additional arguments
    parser.add_argument("--topic-only", action="store_true", help="Only generate a topic without creating a video")
    parser.add_argument("--word-count", type=int, default=1000, help="Desired word count for the transcript")
    parser.add_argument("--output-name", type=str, help="Output filename (optional)")
    parser.add_argument("--model", type=str, help="OpenAI model to use (optional, uses default if not specified)")
    parser.add_argument("--youtube-short", action="store_true", help="Create a YouTube Short instead of a regular video")
    parser.add_argument("--structured", action="store_true", help="Generate a structured essay with intro, body, conclusion")
    parser.add_argument("--num-subtopics", type=int, default=3, help="Number of subtopics to auto-generate for structured transcripts")
    parser.add_argument("--skip-research", action="store_true", help="Skip finding relevant research for faster generation")
    
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
            print(f"Generating {'YouTube Short' if args.youtube_short else 'video'} from theme: {args.theme}")
            success, result, topic = generate_and_create_video(
                theme=args.theme,
                word_count=args.word_count,
                output_name=args.output_name,
                model=args.model,
                youtube_short=args.youtube_short,
                structured=args.structured,
                num_subtopics=args.num_subtopics,
                skip_research=args.skip_research
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
        print(f"Generating {'YouTube Short' if args.youtube_short else 'video'} with topic: {args.topic}")
        result = generate_full_video(
            topic=args.topic,
            word_count=args.word_count,
            output_name=args.output_name,
            youtube_short=args.youtube_short,
            structured=args.structured,
            num_subtopics=args.num_subtopics,
            skip_research=args.skip_research
        )
        print(result)

if __name__ == "__main__":
    main()
