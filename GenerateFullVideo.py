import os
import sys
import subprocess
import logging
import datetime
import argparse
import re
from pathlib import Path
from dotenv import load_dotenv
import GenerateTopicIdea  # Import the topic generator module

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

def verify_file_exists(filepath, min_size=0, error_msg=None):
    """Verify that a file exists and optionally has a minimum size"""
    logger.info(f"Verifying file: {filepath}")
    if not os.path.exists(filepath):
        if error_msg:
            logger.error(error_msg)
        else:
            logger.error(f"File not found: {filepath}")
        return False
    
    if min_size > 0:
        file_size = os.path.getsize(filepath)
        logger.info(f"File size of {filepath}: {file_size} bytes")
        if file_size < min_size:
            logger.error(f"File {filepath} is too small: {file_size} bytes (minimum expected: {min_size})")
            return False
    
    logger.info(f"File verification successful: {filepath}")
    return True

def verify_directory_exists(dirpath, min_files=0, error_msg=None):
    """Verify that a directory exists and optionally has a minimum number of files"""
    logger.info(f"Verifying directory: {dirpath}")
    if not os.path.exists(dirpath):
        if error_msg:
            logger.error(error_msg)
        else:
            logger.error(f"Directory not found: {dirpath}")
        return False
    
    if not os.path.isdir(dirpath):
        logger.error(f"Path is not a directory: {dirpath}")
        return False
    
    if min_files > 0:
        files = os.listdir(dirpath)
        num_files = len(files)
        logger.info(f"Directory {dirpath} contains {num_files} files/subdirectories")
        
        # List all files in the directory for better diagnostics
        if files:
            logger.info(f"Files in {dirpath}:")
            empty_files = []
            for file in files:
                file_path = os.path.join(dirpath, file)
                file_size = os.path.getsize(file_path)
                logger.info(f"  - {file} ({file_size} bytes)")
                if file_size == 0:
                    empty_files.append(file)
            
            # Log warning for empty files
            if empty_files:
                logger.error(f"Empty files found in {dirpath}: {', '.join(empty_files)}")
        else:
            logger.info(f"Directory {dirpath} is empty")
            
        if num_files < min_files:
            logger.error(f"Directory {dirpath} has too few files: {num_files} (minimum expected: {min_files})")
            return False
    
    logger.info(f"Directory verification successful: {dirpath}")
    return True

def run_step(command, step_name, verify_file=None, min_file_size=0, verify_dir=None, min_files=0):
    """
    Run a pipeline step as a subprocess and verify its completion
    
    Args:
        command: The command to execute
        step_name: Name of the step for logging
        verify_file: Optional file to check if it exists after command execution
        min_file_size: Minimum size the verify_file should have
        verify_dir: Optional directory to check if it exists after command execution
        min_files: Minimum number of files the verify_dir should have
        
    Returns:
        bool: Whether the step completed successfully
    """
    logger.info(f"Starting step: {step_name}")
    logger.info(f"Running command: {command}")
    
    try:
        # Run the command with subprocess
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True,
            encoding='utf-8',  # Explicitly specify UTF-8 encoding
            errors='replace'   # Replace any characters that can't be decoded
        )
        
        # Use communicate() instead of manually reading to avoid deadlocks
        stdout, stderr = process.communicate()
        
        # Log the output
        for line in stdout.splitlines():
            if line.strip():
                logger.info(line.strip())
        
        # Get the return code
        return_code = process.returncode
        
        # Check return code
        if return_code != 0:
            logger.error(f"Step '{step_name}' failed with return code {return_code}")
            if stderr:
                logger.error(f"Error output: {stderr}")
            return False
            
        logger.info(f"Step '{step_name}' completed with return code {return_code}")
        
        # Verify output file if specified
        if verify_file:
            if not verify_file_exists(verify_file, min_file_size):
                logger.error(f"Step '{step_name}' failed: Expected output file '{verify_file}' not found or too small")
                return False
        
        # Verify output directory if specified
        if verify_dir:
            if not verify_directory_exists(verify_dir, min_files):
                logger.error(f"Step '{step_name}' failed: Expected output directory '{verify_dir}' not found or has too few files")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error executing step '{step_name}': {str(e)}")
        return False

def get_user_input(prompt, default=None, options=None, allow_empty=False):
    """
    Get input from the user with a prompt and optional validation
    
    Args:
        prompt: The prompt to display to the user
        default: Optional default value if user presses Enter
        options: Optional list of valid options
        allow_empty: Whether to allow empty input
        
    Returns:
        str: The user input
    """
    # Add default value to prompt if provided
    if default is not None:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
        
    # Add options to prompt if provided
    if options:
        option_str = "/".join(options)
        prompt = f"{prompt} ({option_str}) "
    
    while True:
        user_input = input(prompt).strip()
        
        # Use default if input is empty
        if not user_input and default is not None:
            return default
            
        # Check if empty input is allowed
        if not user_input and not allow_empty:
            print("Input cannot be empty. Please try again.")
            continue
            
        # Check if input is in options
        if options and user_input and user_input not in options:
            print(f"Input must be one of: {', '.join(options)}. Please try again.")
            continue
            
        return user_input

def get_user_confirmation(prompt="Do you want to continue?"):
    """Get a yes/no confirmation from the user"""
    response = get_user_input(f"{prompt} (y/n, Enter=y)", default="y", options=["y", "n", "Y", "N"]).lower()
    return response == "y"

def sanitize_filename(filename):
    """
    Sanitize a filename by removing invalid characters and ensuring it's compatible with Windows file systems
    """
    logger.info(f"Sanitizing filename: {filename}")
    
    # Replace invalid characters with underscores
    # Windows doesn't allow: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"\/\\|?*]', '_', filename)
    
    # Ensure the filename isn't just periods (Windows restriction)
    if sanitized.strip('.') == '':
        sanitized = 'untitled'
    
    # Trim leading/trailing whitespace and periods (Windows restriction)
    sanitized = sanitized.strip(' .')
    
    logger.info(f"Sanitized filename: {sanitized}")
    return sanitized

def generate_full_video(args=None):
    """
    Run the full video generation pipeline with user inputs or provided args
    
    Args:
        args: Optional argparse namespace with command line arguments
        
    Returns:
        str: success or error message
    """
    print("\n" + "="*80)
    print(" "*30 + "VIDEO GENERATOR")
    print("="*80 + "\n")
    
    # Use command line args if provided, otherwise prompt for inputs
    if args:
        # Check for topic generation
        if args.generate_topic:
            logger.info(f"Generating a topic based on theme: {args.theme}")
            generated_topic = GenerateTopicIdea.generate_topic_idea(args.theme, model=args.topic_model)
            if not generated_topic:
                return "Error: Failed to generate a topic. Check pipeline.log for details."
            
            # Use the generated topic
            topic = generated_topic
            logger.info(f"Using generated topic: {topic}")
            print(f"Generated topic: {topic}")
        else:
            topic = args.topic
            
        word_count = args.word_count
        youtube_short = args.youtube_short
        structured = args.structured
        num_subtopics = args.num_subtopics
        skip_research = args.skip_research
        output_name = args.output_name
    else:
        # Ask if user wants to generate a topic
        generate_topic = get_user_confirmation("Would you like to generate a topic instead of entering one?")
        
        if generate_topic:
            # Get theme from user
            theme = get_user_input("Enter a theme or category for topic generation", allow_empty=False)
            
            # Generate the topic
            logger.info(f"Generating a topic based on theme: {theme}")
            generated_topic = GenerateTopicIdea.generate_topic_idea(theme)
            
            if not generated_topic:
                if not get_user_confirmation("Failed to generate a topic. Would you like to enter a topic manually?"):
                    return "Error: Topic generation failed and user cancelled manual entry."
                generate_topic = False
            else:
                # Confirm the generated topic
                print(f"\nGenerated topic: {generated_topic}")
                if get_user_confirmation("Do you want to use this topic?"):
                    topic = generated_topic
                else:
                    generate_topic = False
        
        # Get topic from user if not generated or generated topic rejected
        if not generate_topic:
            topic = get_user_input("Enter the topic for your video", allow_empty=False)
        
        # Get word count
        word_count = get_user_input("Enter desired word count for the transcript", default="1000")
        try:
            word_count = int(word_count)
        except ValueError:
            logger.warning(f"Invalid word count '{word_count}', using default of 1000")
            word_count = 1000
        
        # Option for YouTube Short
        youtube_short = get_user_confirmation("Generate a YouTube Short instead of a regular video?")
        
        # Option for structured essay format
        
        if youtube_short:
            structured = False
        else:
            structured = get_user_confirmation("Generate a structured essay format with intro, body, and conclusion?")
        
        # Number of subtopics if structured
        num_subtopics = 3
        if structured:
            subtopics_input = get_user_input("Number of subtopics for the structured format", default="3")
            try:
                num_subtopics = int(subtopics_input)
                if num_subtopics < 1:
                    num_subtopics = 3
                    logger.warning("Number of subtopics must be at least 1, using default of 3")
            except ValueError:
                logger.warning(f"Invalid number of subtopics '{subtopics_input}', using default of 3")
        
        # Skip research option
        skip_research = get_user_confirmation("Skip research for faster generation (but potentially less accurate)?")
        
        # Output name
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        if youtube_short:
            default_output = f"short_{topic.lower().replace(' ', '_')}_{timestamp}"
        else:
            default_output = f"video_{topic.lower().replace(' ', '_')}_{timestamp}"
        output_name = get_user_input("Enter output filename (without extension)", default=default_output)
        
        # Sanitize the output filename
        output_name = sanitize_filename(output_name)
    
    # Verify that required environment variables are set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OpenAI API key not set. Please set it in your environment variables or .env file.")
        if args and args.non_interactive:
            return "Error: OpenAI API key not set. Please set it in your environment variables or .env file."
        elif not args and not get_user_confirmation("OpenAI API key not found. Do you want to continue anyway?"):
            return "Error: OpenAI API key not set. Please set it in your environment variables or .env file."
    
    print("\n" + "="*80)
    print("Pipeline Configuration:")
    print(f"- Topic: {topic}")
    print(f"- Word Count: {word_count}")
    print(f"- YouTube Short: {'Yes' if youtube_short else 'No'}")
    print(f"- Structured Format: {'Yes' if structured else 'No'}")
    if structured:
        print(f"- Number of Subtopics: {num_subtopics}")
    print(f"- Skip Research: {'Yes' if skip_research else 'No'}")
    print(f"- Output Name: {output_name}")
    print("="*80 + "\n")
    
    if not args or not args.non_interactive:
        if not get_user_confirmation("Ready to start video generation. Continue?"):
            return "Video generation cancelled by user."
    
    logger.info("Starting video generation pipeline")
    logger.info(f"Configuration: topic='{topic}', word_count={word_count}, youtube_short={youtube_short}, structured={structured}, num_subtopics={num_subtopics}, skip_research={skip_research}, output_name='{output_name}'")
    
    # Step 0: Run cleanup to start with fresh folders
    logger.info("Step 0/9: Cleaning up project folders before starting...")
    if not run_step(
        "python CleanupProject.py --preserve-output",
        "Cleanup Project"
    ):
        logger.warning("Cleanup step failed, but continuing with video generation")
    
    # Step 1: Generate transcript
    step_args = f"--topic \"{topic}\" --word-count {word_count}"
    if skip_research:
        step_args += " --skip-research"
    
    if structured:
        step_args += f" --structured --num-subtopics {num_subtopics}"
    
    if not run_step(
        f"python VideoTranscriptGenerator.py {step_args}",
        "Generate Transcript",
        verify_dir="Transcript",
        min_files=1
    ):
        return "Error: Failed to generate transcript. Check pipeline.log for details."
    
    
    
    # Step 2: Separate transcript into scenes
    if not run_step(
        "python TranscriptSeperator.py",
        "Separate Transcript",
        verify_dir="Transcript",
        min_files=1
    ):
        return "Error: Failed to separate transcript into scenes. Check pipeline.log for details."
    
    # Step 3: Create narration
    if not run_step(
        "python CreateNarration.py",
        "Create Narration",
        verify_dir="Audio",
        min_files=1
    ):
        return "Error: Failed to create narration. Check pipeline.log for details."
    
    # Step 4: Parse transcripts to CSV
    if not run_step(
        "python ParseTranscriptsToCsv.py",
        "Parse Transcripts to CSV",
        verify_file="transcripts_data.csv",
        min_file_size=5
    ):
        return "Error: Failed to parse transcripts to CSV. Check pipeline.log for details."
    
    # Step 5: Match audio to transcript in CSV
    if not run_step(
        "python MatchAudioToTranscriptInCsv.py",
        "Match Audio to Transcript",
        verify_file="transcripts_data.csv",
        min_file_size=10
    ):
        return "Error: Failed to match audio to transcript. Check pipeline.log for details."
    
    # Step 6: Set transcript CSV length
    if not run_step(
        "python SetTranscriptCsvLength.py",
        "Set Transcript CSV Length",
        verify_file="transcripts_data.csv",
        min_file_size=10
    ):
        return "Error: Failed to set transcript CSV length. Check pipeline.log for details."
    
    # Step 7: Generate scenes
    logger.info("Step 7/9: Running scene generation...")
    scene_generation_success = run_step(
        "python GenerateScenes.py",
        "Generate Scenes",
        verify_dir="Scenes",
        min_files=0  # We allow zero files as sometimes there might be no suitable clips
    )
    
    if not scene_generation_success:
        logger.warning("Scene generation may have issues but continuing to next step")
        if not os.path.exists("Scenes"):
            os.makedirs("Scenes")
            logger.info("Created empty Scenes directory to continue pipeline")
    
    # Verify Scenes directory and contents explicitly with detailed logging
    logger.info("Verifying Scenes directory and content...")
    if not os.path.exists("Scenes"):
        logger.error("Scenes directory not found even after attempted creation")
        return "Error: Scenes directory not found. Check pipeline.log for details."
    
    # Check if Scenes directory is empty
    scenes_files = os.listdir("Scenes") if os.path.exists("Scenes") else []
    logger.info(f"Found {len(scenes_files)} files in Scenes directory: {', '.join(scenes_files) if scenes_files else 'No files'}")
    
    if not scenes_files:
        logger.error("No scene files were generated")
        return "Error: No scene files were generated. Check pipeline.log for details."
    
    # Step 8: Create YouTube Short or Regular Video
    if youtube_short:
        if not run_step(
            f"python MakeYoutubeShort.py --output {output_name}",
            "Create YouTube Short",
            verify_file=f"Output/{output_name}.mp4"
        ):
            return "Error: Failed to create YouTube Short. Check pipeline.log for details."
    else:
        if not run_step(
            f"python Combine.py --output {output_name}",
            "Combine Media",
            verify_file=f"Output/{output_name}.mp4"
        ):
            return "Error: Failed to combine media. Check pipeline.log for details."
    
    # Update the changelog
    update_changelog(topic, youtube_short, structured, output_name)
    
    # Final success message
    final_output = f"Output/{output_name}.mp4"
    if os.path.isfile(final_output):
        file_size = os.path.getsize(final_output) / (1024 * 1024)  # Convert to MB
        logger.info(f"Success! Generated {file_size:.2f}MB {'YouTube Short' if youtube_short else 'video'}: {final_output}")
        return f"Successfully generated {'YouTube Short' if youtube_short else 'video'}: {final_output}"
    else:
        return f"Warning: Process completed but output file not found: {final_output}"

def update_changelog(topic, youtube_short, structured, output_name):
    """Update the Changelog.txt file with the latest generation"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Sanitize topic for display in changelog
        safe_topic = topic.replace("\n", " ").replace("\r", "")
        entry = f"[{timestamp}] Generated {'YouTube Short' if youtube_short else 'video'} on topic: '{safe_topic}' "
        entry += f"({'structured format' if structured else 'standard format'}) - Output: {output_name}.mp4\n"
        
        # Create changelog if it doesn't exist
        if not os.path.exists("Changelog.txt"):
            with open("Changelog.txt", "w", encoding="utf-8") as f:
                f.write("# YouTube Video Generator Changelog\n\n")
        
        # Append to changelog
        with open("Changelog.txt", "a", encoding="utf-8") as f:
            f.write(entry)
            
        logger.info("Updated Changelog.txt")
    except Exception as e:
        logger.error(f"Failed to update changelog: {str(e)}")

def print_pipeline_steps():
    """Print the full pipeline steps for reference"""
    print("\nFull Video Generation Pipeline Steps:")
    print("0. GenerateTopicIdea.py - (Optional) Generate a topic based on a theme")
    print("1. VideoTranscriptGenerator.py - Generate transcript")
    print("2. TranscriptSeperator.py - Separate transcript into scenes")
    print("3. CreateNarration.py - Create audio narration")
    print("4. ParseTranscriptsToCsv.py - Parse transcripts to CSV")
    print("5. MatchAudioToTranscriptInCsv.py - Match audio to transcript in CSV")
    print("6. SetTranscriptCsvLength.py - Set transcript CSV length")
    print("7. GenerateScenes.py - Generate video scenes")
    print("8. Combine.py or MakeYoutubeShort.py - Create final video")
    print("9. CleanupProject.py - Clean up temporary files")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate a complete video from transcript to final output")
    
    # Main arguments
    parser.add_argument("--topic", type=str, help="Main topic for the video")
    parser.add_argument("--word-count", type=int, default=1000, help="Desired word count for the transcript")
    parser.add_argument("--output-name", type=str, help="Output filename (without extension)")
    parser.add_argument("--youtube-short", action="store_true", help="Create a YouTube Short instead of a regular video")
    parser.add_argument("--structured", action="store_true", help="Generate a structured essay with intro, body, conclusion")
    parser.add_argument("--num-subtopics", type=int, default=3, help="Number of subtopics to auto-generate for structured transcripts")
    parser.add_argument("--skip-research", action="store_true", help="Skip finding relevant research for faster generation")
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode without prompting for input")
    
    # Topic generation arguments
    parser.add_argument("--generate-topic", action="store_true", help="Generate a topic idea instead of providing one")
    parser.add_argument("--theme", type=str, help="Theme to use for topic generation when --generate-topic is specified")
    parser.add_argument("--topic-model", type=str, help="OpenAI model to use for topic generation (optional)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate arguments for non-interactive mode
    if args.non_interactive and not args.topic and not (args.generate_topic and args.theme):
        parser.error("Either --topic or (--generate-topic and --theme) is required when using --non-interactive")
    
    # Sanitize output_name if provided
    if args.output_name:
        args.output_name = sanitize_filename(args.output_name)
    
    return args

def main():
    """Main entry point for the script"""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Print the pipeline steps for reference
    if not args.non_interactive:
        print_pipeline_steps()
    
    # Run the video generation process
    if (args.topic or args.generate_topic and args.theme) and args.non_interactive:
        # Run in non-interactive mode with provided arguments
        result = generate_full_video(args)
    else:
        # Run in interactive mode
        result = generate_full_video()
    
    print("\n" + "="*80)
    print(result)
    print("="*80 + "\n")
    
    # Return success/failure for external scripts
    if result.startswith("Error:") or result.startswith("Warning:"):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

