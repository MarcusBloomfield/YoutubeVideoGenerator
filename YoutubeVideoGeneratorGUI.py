import eel
import os
import sys
import io
import time
import threading
import datetime
from contextlib import redirect_stdout

# Import project modules
import VideoTranscriptGenerator
import Mp4ClipsExtractor
import SetClipCsvKeywords
import ParseClipsToCsv
import CreateNarration
import TranscriptSeperator
import ParseTranscriptsToCsv
import MatchAudioToTranscriptInCsv
import SetTranscriptCsvLength
import GenerateScenes
import Combine
import ExpandTranscript
import Research
import TranscriptPurifier
import PurifyClipsData
import OpenAiQuerying
import RawVideoRenamer
import CleanupProject
import GenerateFullVideo
from dotenv import load_dotenv

# Initialize Eel
eel.init('web')

# Load environment variables
load_dotenv()

# Global variables to store captured output
captured_output = ""

# Custom stdout handler to capture and log output
class LoggingStreamHandler(io.StringIO):
    def __init__(self):
        super().__init__()
    
    def write(self, text):
        super().write(text)
        if text.strip():  # Only log non-empty lines
            eel.add_log(text.strip(), 'info')
    
    def flush(self):
        pass

# Helper function to log messages to the frontend
def log_message(message, level='info'):
    """Log a message to the frontend"""
    eel.add_log(message, level)
    print(message)

# Helper function to capture stdout and return as string
def capture_stdout(func, *args, **kwargs):
    global captured_output
    captured_output = ""
    
    # Create a custom stream handler that logs output
    stream_handler = LoggingStreamHandler()
    
    # Redirect stdout to our custom handler
    with redirect_stdout(stream_handler):
        try:
            result = func(*args, **kwargs)
            # Get the captured output
            captured_output = stream_handler.getvalue()
            return captured_output
        except Exception as e:
            log_message(f"Error in {func.__name__}: {str(e)}", 'error')
            raise e

# Function to update progress
def update_progress(percent, message=None):
    eel.update_progress(percent, message)
    if message:
        log_message(f"Progress {percent}%: {message}")
    time.sleep(0.1)  # Small delay to allow UI to update

# Exposed functions for the UI
@eel.expose
def set_api_key(api_key):
    """Set the OpenAI API key"""
    log_message("Setting OpenAI API key...")
    os.environ["OPENAI_API_KEY"] = api_key
    with open(".env", "w") as f:
        f.write(f"OPENAI_API_KEY={api_key}\n")
    log_message("API key set successfully", 'info')
    return "API key set successfully"

@eel.expose
def generate_transcript(topic, word_count=1000):
    """Generate a transcript with the given topic and word count"""
    if not os.environ.get("OPENAI_API_KEY"):
        log_message("Error: OpenAI API key not set", 'error')
        return "Error: OpenAI API key not set. Please set it in the Settings tab."
    
    # Progress updates
    log_message(f"Generating transcript for topic: {topic} with {word_count} words", 'info')
    update_progress(10, "Starting transcript generation...")
    
    try:
        # Convert word_count to integer if it's a string
        if isinstance(word_count, str):
            word_count = int(word_count)
            
        # Update progress
        update_progress(20, "Generating transcript...")
        
        # Capture the output of the function
        output = capture_stdout(
            VideoTranscriptGenerator.generate_transcript,
            topic=topic,
            word_count=word_count
        )
        
        # Final progress update
        update_progress(100, "Transcript generation complete!")
        log_message("Transcript generation completed successfully", 'info')
        
        return output
    except Exception as e:
        log_message(f"Error generating transcript: {str(e)}", 'error')
        return f"Error: {str(e)}"

@eel.expose
def purify_clips_data():
    """Run the clips data purification process"""
    log_message("Starting clips data purification...", 'info')
    update_progress(10, "Starting clips data purification...")
    
    try:
        output = capture_stdout(PurifyClipsData.purify_clips_data)
        update_progress(100, "Clips data purification complete!")
        log_message("Clips data purification completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error purifying clips data: {str(e)}", 'error')
        return f"Error: {str(e)}"

@eel.expose
def extract_clips():
    """Extract clips from the raw video files"""
    log_message("Starting clip extraction...", 'info')
    update_progress(10, "Starting clip extraction...")
    
    try:
        mp4_extractor = Mp4ClipsExtractor.Mp4ClipsExtractor()
        output = capture_stdout(mp4_extractor.main)
        update_progress(100, "Clip extraction complete!")
        log_message("Clip extraction completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error extracting clips: {str(e)}", 'error')
        return f"Error: {str(e)}"

@eel.expose
def set_clip_keywords():
    """Set keywords for clips"""
    log_message("Starting keyword setting...", 'info')
    update_progress(10, "Starting keyword setting...")
    
    try:
        keyword_setter = SetClipCsvKeywords.SetClipCsvKeywords()
        output = capture_stdout(keyword_setter.main)
        update_progress(100, "Keyword setting complete!")
        log_message("Keyword setting completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error setting keywords: {str(e)}", 'error')
        return f"Error: {str(e)}"

@eel.expose
def parse_to_csv():
    """Parse clips to CSV"""
    log_message("Starting parsing to CSV...", 'info')
    update_progress(10, "Starting parsing to CSV...")
    
    try:
        parser = ParseClipsToCsv.ParseClipsToCsv()
        output = capture_stdout(parser.main)
        update_progress(100, "Parsing to CSV complete!")
        log_message("Parsing to CSV completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error parsing to CSV: {str(e)}", 'error')
        return f"Error: {str(e)}"

@eel.expose
def generate_scenes():
    """Generate scenes from the clips and transcript"""
    log_message("Starting scene generation...", 'info')
    update_progress(10, "Starting scene generation...")
    
    try:
        # Capture output from all steps
        all_output = []
        
        # Step 2: Parse transcripts to CSV
        log_message("Parsing transcripts to CSV...", 'info')
        update_progress(30, "Parsing transcripts to CSV...")
        all_output.append("\n=== PARSING TRANSCRIPTS TO CSV ===")
        try:
            all_output.append(capture_stdout(ParseTranscriptsToCsv.main))
        except Exception as e:
            log_message(f"Error in ParseTranscriptsToCsv: {str(e)}", 'error')
            all_output.append(f"ERROR: {str(e)}")
        
        # Step 3: Match audio to transcript in CSV
        log_message("Matching audio to transcript in CSV...", 'info')
        update_progress(45, "Matching audio to transcript in CSV...")
        all_output.append("\n=== MATCHING AUDIO TO TRANSCRIPT ===")
        try:
            all_output.append(capture_stdout(MatchAudioToTranscriptInCsv.match_audio_to_transcript))
        except Exception as e:
            log_message(f"Error in MatchAudioToTranscriptInCsv: {str(e)}", 'error')
            all_output.append(f"ERROR: {str(e)}")
        
        # Step 4: Set transcript CSV length
        log_message("Setting transcript CSV length...", 'info')
        update_progress(60, "Setting transcript CSV length...")
        all_output.append("\n=== SETTING TRANSCRIPT CSV LENGTH ===")
        
        try:
            # Create a function to call the transcript length function safely
            def update_lengths():
                csv_file_path = "transcripts_data.csv"
                return SetTranscriptCsvLength.update_csv_with_audio_lengths(csv_file_path)
                
            all_output.append(capture_stdout(update_lengths))
        except Exception as e:
            log_message(f"Error in SetTranscriptCsvLength: {str(e)}", 'error')
            all_output.append(f"ERROR: {str(e)}")
        
        # Step 5: Generate scenes
        log_message("Generating scenes from clips and transcript...", 'info')
        update_progress(80, "Generating scenes from clips and transcript...")
        all_output.append("\n=== GENERATING SCENES ===")
        try:
            scene_generator = GenerateScenes.GenerateScenes()
            all_output.append(capture_stdout(scene_generator.main))
        except Exception as e:
            log_message(f"Error in GenerateScenes: {str(e)}", 'error')
            all_output.append(f"ERROR: {str(e)}")
        
        # Join all output
        combined_output = "\n".join(all_output)
        
        update_progress(100, "Scene generation complete!")
        log_message("Scene generation completed successfully", 'info')
        return combined_output
    except Exception as e:
        error_msg = f"Error generating scenes: {str(e)}"
        log_message(error_msg, 'error')
        return error_msg

@eel.expose
def create_narration():
    """Create narration from the transcript"""
    log_message("Starting narration creation...", 'info')
    update_progress(10, "Starting narration creation...")
    
    try:
        # Capture output from all steps
        all_output = []
        
        # Step 1: Process all transcripts with TranscriptSeperator
        log_message("Processing transcripts with TranscriptSeperator...", 'info')
        update_progress(30, "Processing transcripts...")
        all_output.append("=== PROCESSING TRANSCRIPTS ===")
        try:
            all_output.append(capture_stdout(TranscriptSeperator.process_all_transcripts))
        except Exception as e:
            log_message(f"Error in TranscriptSeperator: {str(e)}", 'error')
            all_output.append(f"ERROR: {str(e)}")
        
        # Step 2: Create narration
        log_message("Creating narration audio files...", 'info')
        update_progress(60, "Creating narration...")
        all_output.append("\n=== CREATING NARRATION ===")
        try:
            narration_creator = CreateNarration.CreateNarration()
            all_output.append(capture_stdout(narration_creator.process_transcripts))
        except Exception as e:
            log_message(f"Error in CreateNarration: {str(e)}", 'error')
            all_output.append(f"ERROR: {str(e)}")
        
        # Join all output
        combined_output = "\n".join(all_output)
        
        update_progress(100, "Narration creation complete!")
        log_message("Narration creation completed successfully", 'info')
        return combined_output
    except Exception as e:
        error_msg = f"Error creating narration: {str(e)}"
        log_message(error_msg, 'error') 
        return error_msg

@eel.expose
def combine_media(output_name=None):
    """Combine video and audio files"""
    log_message("Starting media combination...", 'info')
    update_progress(10, "Starting media combination...")
    
    if output_name:
        log_message(f"Using custom output name: {output_name}", 'info')
    
    try:
        combiner = Combine.Combine()
        output = capture_stdout(combiner.main, output_name)
        update_progress(100, "Media combination complete!")
        log_message("Media combination completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error combining media: {str(e)}", 'error')
        return f"Error: {str(e)}"

# NEW: Research tab functionality
@eel.expose
def research_topic(topic, urls, loops=1):
    """Research a topic using the provided URLs"""
    if not os.environ.get("OPENAI_API_KEY"):
        log_message("Error: OpenAI API key not set", 'error')
        return "Error: OpenAI API key not set. Please set it in the Settings tab."
    
    log_message(f"Starting research for topic: {topic}", 'info')
    log_message(f"URLs to research: {urls}", 'info')
    log_message(f"Research loops: {loops}", 'info')
    update_progress(10, "Starting research process...")
    
    try:
        # Convert the comma-separated URLs to a list
        url_list = [url.strip() for url in urls.split(',') if url.strip()]
        
        if not url_list:
            log_message("Error: No valid URLs provided", 'error')
            return "Error: No valid URLs provided."
        
        update_progress(30, f"Researching topic '{topic}' from {len(url_list)} URLs...")
        
        # Call Research module
        output = capture_stdout(
            Research.research_topic,
            url_list,
            topic
        )
        
        update_progress(100, "Research complete!")
        log_message("Research completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error during research: {str(e)}", 'error')
        return f"Error: {str(e)}"

# NEW: Transcript Expansion functionality
@eel.expose
def expand_transcript_file(transcript_file, loops=1, words_needed=1000):
    """Expand a transcript file with additional content"""
    if not os.environ.get("OPENAI_API_KEY"):
        log_message("Error: OpenAI API key not set", 'error')
        return "Error: OpenAI API key not set. Please set it in the Settings tab."
    
    transcript_path = os.path.join("Transcript", transcript_file)
    
    # Check if the transcript file exists
    if not os.path.exists(transcript_path):
        log_message(f"Error: Transcript file {transcript_file} not found", 'error')
        return f"Error: Transcript file {transcript_file} not found."
    
    log_message(f"Starting transcript expansion of {transcript_file}", 'info')
    log_message(f"Expansion loops: {loops}, Target words: {words_needed}", 'info')
    update_progress(10, f"Starting transcript expansion of {transcript_file}...")
    
    try:
        # Convert parameters to integers
        loops = int(loops)
        words_needed = int(words_needed)
        
        # Call ExpandTranscript module
        output = capture_stdout(
            ExpandTranscript.expand_transcript,
            transcript_path,
            loops,
            words_needed=words_needed
        )
        
        update_progress(100, "Transcript expansion complete!")
        log_message("Transcript expansion completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error expanding transcript: {str(e)}", 'error')
        return f"Error: {str(e)}"

@eel.expose
def get_transcript_files():
    """Get a list of transcript files in the Transcript directory"""
    transcript_dir = "Transcript"
    
    log_message("Getting list of transcript files...", 'info')
    if not os.path.exists(transcript_dir):
        log_message(f"Creating transcript directory: {transcript_dir}", 'info')
        os.makedirs(transcript_dir)
        return []
    
    transcript_files = [f for f in os.listdir(transcript_dir) 
                      if f.endswith('.txt') and os.path.isfile(os.path.join(transcript_dir, f))]
    
    log_message(f"Found {len(transcript_files)} transcript files", 'info')
    return transcript_files

# NEW: Raw Video Management functionality
@eel.expose
def rename_raw_videos(append_string="_processed"):
    """Rename raw video files in the RawVideo directory"""
    log_message(f"Starting raw video renaming with append string: '{append_string}'", 'info')
    update_progress(10, "Starting raw video renaming process...")
    
    try:
        output = capture_stdout(
            RawVideoRenamer.rename_video_files,
            directory="RawVideo",
            append_string=append_string
        )
        
        update_progress(100, "Raw video renaming complete!")
        log_message("Raw video renaming completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error renaming raw videos: {str(e)}", 'error')
        return f"Error: {str(e)}"

@eel.expose
def get_raw_video_files():
    """Get a list of video files in the RawVideo directory"""
    raw_video_dir = "RawVideo"
    
    log_message("Getting list of raw video files...", 'info')
    if not os.path.exists(raw_video_dir):
        log_message(f"Creating raw video directory: {raw_video_dir}", 'info')
        os.makedirs(raw_video_dir)
        return []
    
    # Common video file extensions
    video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm']
    
    video_files = [f for f in os.listdir(raw_video_dir) 
                 if any(f.lower().endswith(ext) for ext in video_extensions)
                 and os.path.isfile(os.path.join(raw_video_dir, f))]
    
    log_message(f"Found {len(video_files)} raw video files", 'info')
    return video_files

# NEW: File Browser functionality
@eel.expose
def get_directory_contents(directory):
    """Get the contents of a directory"""
    log_message(f"Getting contents of directory: {directory}", 'info')
    if not os.path.exists(directory):
        log_message(f"Creating directory: {directory}", 'info')
        os.makedirs(directory)
        return {"directories": [], "files": []}
    
    try:
        directory_contents = {"directories": [], "files": []}
        
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isdir(item_path):
                directory_contents["directories"].append(item)
            elif os.path.isfile(item_path):
                # Get the file size in KB
                size_kb = round(os.path.getsize(item_path) / 1024, 2)
                directory_contents["files"].append({
                    "name": item,
                    "size": f"{size_kb} KB",
                    "modified": time.ctime(os.path.getmtime(item_path))
                })
        
        log_message(f"Found {len(directory_contents['directories'])} directories and {len(directory_contents['files'])} files", 'info')
        return directory_contents
    except Exception as e:
        log_message(f"Error getting directory contents: {str(e)}", 'error')
        return {"error": str(e)}

@eel.expose
def read_file_content(file_path):
    """Read the content of a file"""
    log_message(f"Reading file: {file_path}", 'info')
    try:
        if not os.path.exists(file_path):
            log_message(f"Error: File {file_path} not found", 'error')
            return {"error": f"File {file_path} not found."}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        log_message(f"File read successfully: {file_path}", 'info')
        return {"content": content}
    except Exception as e:
        log_message(f"Error reading file: {str(e)}", 'error')
        return {"error": str(e)}

# NEW: System log functionality
@eel.expose
def get_system_info():
    """Get system information for the log"""
    log_message("Getting system information...", 'info')
    try:
        system_info = {
            "os": sys.platform,
            "python_version": sys.version,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "directories": {
                "transcript": os.path.exists("Transcript"),
                "clips": os.path.exists("Clips"),
                "scenes": os.path.exists("Scenes"),
                "audio": os.path.exists("Audio"),
                "output": os.path.exists("Output"),
                "raw_video": os.path.exists("RawVideo"),
                "research": os.path.exists("Research")
            }
        }
        
        # Check for key files
        system_info["key_files"] = {
            "clips_data.csv": os.path.exists("clips_data.csv"),
            "transcripts_data.csv": os.path.exists("transcripts_data.csv")
        }
        
        log_message("System information collected", 'info')
        return system_info
    except Exception as e:
        log_message(f"Error getting system information: {str(e)}", 'error')
        return {"error": str(e)}

@eel.expose
def get_latest_transcript_content():
    """Get the content of the most recently generated transcript file"""
    log_message("Getting content of the latest transcript file...", 'info')
    transcript_dir = "Transcript"
    
    if not os.path.exists(transcript_dir):
        log_message("Transcript directory not found", 'error')
        return "No transcript files found."
    
    # Find all transcript files
    transcript_files = [f for f in os.listdir(transcript_dir) 
                      if f.endswith('.txt') and os.path.isfile(os.path.join(transcript_dir, f))]
    
    if not transcript_files:
        log_message("No transcript files found", 'warning')
        return "No transcript files found."
    
    # Get the most recently modified file
    latest_file = max(transcript_files, key=lambda f: os.path.getmtime(os.path.join(transcript_dir, f)))
    latest_path = os.path.join(transcript_dir, latest_file)
    
    log_message(f"Found latest transcript file: {latest_file}", 'info')
    
    try:
        with open(latest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        log_message("Successfully read transcript content", 'info')
        return content
    except Exception as e:
        log_message(f"Error reading transcript file: {str(e)}", 'error')
        return f"Error reading transcript file: {str(e)}"

@eel.expose
def generate_full_video(topic, word_count=1000, output_name=None):
    """
    Wrapper function for GenerateFullVideo.generate_full_video
    
    Args:
        topic: The main topic for the video
        word_count: The desired word count for the transcript
        output_name: Optional name for the output video file
        
    Returns:
        A summary of the operations performed
    """
    # Define functions for the CSV processing steps
    def parse_transcripts_to_csv():
        return ParseTranscriptsToCsv.main()
    
    def match_audio_to_transcript():
        return MatchAudioToTranscriptInCsv.match_audio_to_transcript()
    
    def set_transcript_csv_length():
        csv_file_path = "transcripts_data.csv"
        return SetTranscriptCsvLength.update_csv_with_audio_lengths(csv_file_path)
    
    return GenerateFullVideo.generate_full_video(
        topic=topic,
        word_count=word_count,
        output_name=output_name,
        log_message=log_message,
        update_progress=update_progress,
        capture_stdout=capture_stdout,
        generate_transcript=generate_transcript,
        separate_transcript=TranscriptSeperator.process_all_transcripts,
        parse_transcripts_to_csv=parse_transcripts_to_csv,
        match_audio_to_transcript=match_audio_to_transcript,
        set_transcript_csv_length=set_transcript_csv_length,
        create_narration=create_narration,
        generate_scenes=generate_scenes,
        combine_media=combine_media,
        cleanup_project=cleanup_project
    )

@eel.expose
def generate_topic_from_theme(theme):
    """
    Generate a specific topic based on a broader theme
    
    Args:
        theme: The general theme or category (e.g., "World War II", "Space Exploration")
        
    Returns:
        The generated topic or error message
    """
    if not os.environ.get("OPENAI_API_KEY"):
        log_message("Error: OpenAI API key not set", 'error')
        return {"success": False, "message": "OpenAI API key not set. Please set it in the Settings tab."}
    
    log_message(f"Generating topic idea for theme: {theme}", 'info')
    update_progress(10, "Generating topic idea...")
    
    try:
        topic = GenerateFullVideo.generate_topic_idea(theme, log_message)
        
        if not topic:
            log_message("Failed to generate topic", 'error')
            update_progress(0, "")
            return {"success": False, "message": "Failed to generate a topic. Please try again with a different theme."}
        
        log_message(f"Successfully generated topic: {topic}", 'info')
        update_progress(100, "Topic generation complete!")
        return {"success": True, "topic": topic}
    except Exception as e:
        error_msg = f"Error generating topic: {str(e)}"
        log_message(error_msg, 'error')
        update_progress(0, "")
        return {"success": False, "message": error_msg}

@eel.expose
def generate_video_from_theme(theme, word_count=1000, output_name=None):
    """
    Generate a topic from a theme and then create a full video
    
    Args:
        theme: The general theme to generate a topic from
        word_count: The desired word count for the transcript
        output_name: Optional name for the output video file
        
    Returns:
        A summary of the operations performed
    """
    if not os.environ.get("OPENAI_API_KEY"):
        log_message("Error: OpenAI API key not set", 'error')
        return "Error: OpenAI API key not set. Please set it in the Settings tab."
    
    log_message(f"Starting video generation from theme: {theme}", 'info')
    update_progress(5, "Generating topic...")
    
    try:
        success, result, topic = GenerateFullVideo.generate_and_create_video(
            theme=theme,
            word_count=word_count,
            output_name=output_name,
            log_message=log_message,
            update_progress=update_progress
        )
        
        if not success:
            log_message("Failed to generate video from theme", 'error')
            update_progress(0, "")
            return f"Error: {result}"
        
        return f"Generated topic: {topic}\n\n{result}"
    except Exception as e:
        error_msg = f"Error generating video from theme: {str(e)}"
        log_message(error_msg, 'error')
        update_progress(0, "")
        return error_msg

@eel.expose
def cleanup_project():
    """Clean up project directories by removing files from Transcript, Audio, and Scenes folders"""
    log_message("Starting project cleanup...", 'info')
    update_progress(10, "Starting project cleanup...")
    
    try:
        # Capture output from CleanupProject with preserve_output=True to keep videos
        output = capture_stdout(lambda: CleanupProject.clean_project(preserve_output=True))
        
        update_progress(100, "Project cleanup complete!")
        log_message("Project cleanup completed successfully", 'info')
        return output
    except Exception as e:
        log_message(f"Error during project cleanup: {str(e)}", 'error')
        return f"Error: {str(e)}"

# Run the Eel app
def main():
    # Create necessary directories if they don't exist
    directories = ["Transcript", "Clips", "Scenes", "Audio", "Output", "RawVideo", "Research"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        log_message(f"Ensured directory exists: {directory}", 'info')
    
    log_message("YouTube Video Generator GUI started", 'info')
    log_message(f"System: {sys.platform}, Python: {sys.version}", 'info')
    
    # Start Eel
    try:
        eel.start('index.html', size=(1200, 800))
    except (SystemExit, MemoryError, KeyboardInterrupt):
        # Handle graceful shutdown
        log_message("Application shutting down...", 'info')
        pass

if __name__ == "__main__":
    main() 