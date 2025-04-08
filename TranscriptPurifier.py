import os
import logging
import argparse
from pathlib import Path
from OpenAiQuerying import query_openai
from Models import ModelCategories
from Prompts import TRANSCRIPT_PURIFIER_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def purify_transcript(transcript_path, model=ModelCategories.getPurifyTranscriptModel(), preview=False):
    """
    Process a transcript file to ensure content coherence using OpenAI.
    
    Args:
        transcript_path (str): Path to the transcript file
        model (str): OpenAI model to use
        preview (bool): If True, only show what would be changed without saving
        
    Returns:
        tuple: (bool success, str message)
    """
    logger.info(f"Processing transcript: {transcript_path}")
    
    try:
        # Read the transcript file
        with open(transcript_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create the prompt for OpenAI
        prompt = TRANSCRIPT_PURIFIER_PROMPT.format(content=content)
        
        # Query OpenAI for improved content
        logger.info(f"Sending transcript to OpenAI for review ({len(content)} characters)")
        improved_content = query_openai(prompt, model=model)
        
        if not improved_content:
            return False, "Failed to get response from OpenAI"
        
        # If in preview mode, just show the differences
        if preview:
            logger.info("Preview mode - changes would be:")
            if improved_content == content:
                logger.info("No changes needed for this transcript")
            else:
                logger.info("Transcript would be updated with improvements from OpenAI")
            return True, "Preview completed"
        
        # Write the improved content back to the file
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(improved_content)
        
        logger.info(f"Successfully processed and updated {transcript_path}")
        return True, "Transcript updated successfully"
    
    except Exception as e:
        logger.error(f"Error processing {transcript_path}: {e}")
        return False, f"Error: {str(e)}"

def process_all_transcripts(transcript_dir="Transcript", model=ModelCategories.getPurifyTranscriptModel(), preview=False):
    """
    Process all transcript files in the specified directory.
    
    Args:
        transcript_dir (str): Directory containing transcript files
        model (str): OpenAI model to use
        preview (bool): If True, only show what would be changed without saving
    """
    transcript_path = Path(transcript_dir)
    
    if not transcript_path.exists() or not transcript_path.is_dir():
        logger.error(f"Transcript directory not found: {transcript_dir}")
        return
    
    # Get all .txt files in the transcript directory
    transcript_files = list(transcript_path.glob("*.txt"))
    
    if not transcript_files:
        logger.warning(f"No transcript files found in {transcript_dir}")
        return
    
    logger.info(f"Found {len(transcript_files)} transcript files to process")
    
    successful = 0
    failed = 0
    
    for file_path in transcript_files:
        logger.info(f"Processing {file_path.name}...")
        success, message = purify_transcript(str(file_path), model, preview)
        
        if success:
            successful += 1
        else:
            failed += 1
            logger.error(f"Failed to process {file_path.name}: {message}")
    
    logger.info(f"Processing complete. Success: {successful}, Failed: {failed}")

def main():
    parser = argparse.ArgumentParser(description="Process transcript files to ensure content coherence")
    parser.add_argument("--dir", type=str, default="Transcript", help="Directory containing transcript files")
    parser.add_argument("--model", type=str, default=ModelCategories.getPurifyTranscriptModel(), help="OpenAI model to use")
    parser.add_argument("--file", type=str, help="Process a single file instead of all files in the directory")
    parser.add_argument("--preview", action="store_true", help="Preview changes without saving")
    
    args = parser.parse_args()
    
    if args.file:
        # Process a single file
        file_path = args.file
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return
        
        success, message = purify_transcript(file_path, args.model, args.preview)
        if success:
            logger.info(f"Successfully processed {file_path}")
        else:
            logger.error(f"Failed to process {file_path}: {message}")
    else:
        # Process all files in the directory
        process_all_transcripts(args.dir, args.model, args.preview)

if __name__ == "__main__":
    main()
