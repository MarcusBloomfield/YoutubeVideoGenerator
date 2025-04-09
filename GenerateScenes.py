import os
import csv
import subprocess
import pandas as pd
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from OpenAiQuerying import query_openai, check_api_key
import random
import shutil
from Prompts import CLIP_MATCHING_PROMPT, SCENE_GENERATION_PROMPT
from Models import ModelCategories

def ensure_dir(directory):
    """Ensure directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def generate_scenes_by_matching():
    """Generate video scenes by matching transcripts with clips"""
    # Ensure output directory exists
    output_dir = "Scenes"
    ensure_dir(output_dir)
    
    # Ensure transcript archive directory exists
    transcript_archive_dir = os.path.join("Transcript", "old")
    ensure_dir(transcript_archive_dir)
    
    # Configuration variables
    additional_time_buffer = 3  # Additional seconds to add beyond transcript length
    
    # Track which clips have been used (only in memory for this run)
    used_clip_ids = set()
    
    # Check for API key
    api_key = check_api_key()
    if not api_key:
        print("Error: OpenAI API key not found. Cannot proceed with scene generation.")
        return
    
    # Read CSV data
    transcripts_df = pd.read_csv("transcripts_data.csv")
    clips_df = pd.read_csv("clips_data.csv")
    
    # Process each transcript
    for index, transcript in transcripts_df.iterrows():
        transcript_id = transcript['id']
        transcript_length = float(transcript['length'])
        audio_file = transcript['audio_file']
        transcript_file = transcript['transcript_file']
        
        # Extract order number from audio filename (format: "001_transcript-id...")
        order_number = "000"
        if "_" in os.path.basename(audio_file):
            try:
                # Get just the filename without path
                filename = os.path.basename(audio_file)
                order_number = filename.split("_")[0]
            except:
                # Use index as fallback if we can't extract from filename
                order_number = f"{index+1:03d}"
        
        print(f"Processing transcript {transcript_id} with target length {transcript_length}s")
        
        # Read transcript content if available
        transcript_content = ""
        if os.path.exists(transcript_file):
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
            except Exception as e:
                print(f"Error reading transcript file: {e}")
                continue
        else:
            print(f"Transcript file not found: {transcript_file}")
            continue
        
        # Find matching clips using OpenAI to find semantic matches
        selected_clips = []
        current_length = 0
        
        # Filter out already used clips
        remaining_clips = clips_df[~clips_df['id'].isin(used_clip_ids)].copy()
        
        if remaining_clips.empty:
            print("Warning: All clips have been used. Consider adding more content.")
            break
            
        # Build a list of available clips with their keywords for the AI to choose from
        clips_list = []
        for _, clip in remaining_clips.iterrows():
            clips_list.append({
                "id": clip['id'],
                "keywords": clip['keywords'],
                "length": float(clip['length'])
            })
        
        # Create prompt for OpenAI to match clips to transcript
        prompt = CLIP_MATCHING_PROMPT.format(
            transcript_content=transcript_content,
            transcript_length=transcript_length,
            clips_list=clips_list
        )
        
        while current_length <= transcript_length:
            try:
                # Query OpenAI for clip selection
                response = query_openai(prompt, model=ModelCategories.getSceneGenerationModel())
            
            # Parse response to get clip IDs 
                import re
                import json
                # Find anything that looks like a JSON array
                match = re.search(r'\[.*?\]', response, re.DOTALL)
                if match:
                    try:
                        selected_ids = json.loads(match.group(0))
                        # Get the actual clips from our dataframe
                        for clip_id in selected_ids:
                            if clip_id in remaining_clips['id'].values and clip_id not in used_clip_ids:
                                clip = remaining_clips[remaining_clips['id'] == clip_id].iloc[0]
                                selected_clips.append(clip)
                                used_clip_ids.add(clip_id)
                                current_length += float(clip['length'])
                                # Continue adding clips until we have enough
                                # Always ensure clips are longer than transcript length with a buffer
                                if current_length >= transcript_length + additional_time_buffer:
                                    break
                    except json.JSONDecodeError:
                        print(f"Could not parse AI response as JSON {response}")
            except Exception as e:
                print(f"Error using OpenAI for clip matching: {e}")
        
        if not selected_clips:
            print(f"No suitable clips found for transcript {transcript_id}")
            continue
            
        if current_length <= transcript_length:
            print(f"Warning: Could not find enough clips to exceed transcript length. Using available clips anyway.")
            
        print(f"Selected {len(selected_clips)} clips with total length {current_length}s for transcript length {transcript_length}s")
        
        # Combine clips with audio
        output_file = os.path.join(output_dir, f"{order_number}_scene_{transcript_id}.mp4")
        success = combine_clips_with_audio(selected_clips, audio_file, output_file)
        
        if success:
            print(f"Created scene: {output_file}")
            
            # Move transcript file to archive directory
            if os.path.exists(transcript_file):
                transcript_filename = os.path.basename(transcript_file)
                archive_path = os.path.join(transcript_archive_dir, transcript_filename)
                try:
                    shutil.move(transcript_file, archive_path)
                    print(f"Moved transcript to {archive_path}")
                except Exception as e:
                    print(f"Error moving transcript file: {e}")
        
    # Print summary at the end
    print(f"Generation complete. Used {len(used_clip_ids)} unique clips across all scenes.")

def combine_clips_with_audio(clips, audio_file, output_file):
    """Combine video clips with audio file into a single MP4"""
    try:
        # Load all video clips
        video_clips = []
        for clip in clips:
            video_path = clip['filelocation']
            video = VideoFileClip(video_path)
            # Mute the original video to avoid audio overlap
            video = video.without_audio()
            video_clips.append(video)
        
        # Concatenate video clips
        final_clip = concatenate_videoclips(video_clips)
        
        # Load the audio
        print(f"Adding audio from: {audio_file}")
        audio = AudioFileClip(audio_file)
        
        # Verify audio loaded correctly
        if audio is None:
            print(f"Error: Audio could not be loaded from {audio_file}")
            return False
        
        print(f"Audio duration: {audio.duration}, Video duration: {final_clip.duration}")
        
        # Ensure audio doesn't exceed video duration
        if audio.duration > final_clip.duration:
            audio = audio.subclipped(0, final_clip.duration)
        
        # Create final clip with audio
        final_clip_with_audio = final_clip.with_audio(audio)
        
        # Write the output file
        final_clip_with_audio.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Close all clips to free memory
        final_clip.close()
        for clip in video_clips:
            clip.close()
        audio.close()
        final_clip_with_audio.close()
        
        print(f"Successfully created: {output_file}")
        return True
    except Exception as e:
        print(f"Error creating scene: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_scenes_by_matching()
