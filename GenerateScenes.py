import os
import csv
import subprocess
import pandas as pd
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from OpenAiQuerying import query_openai, check_api_key

def ensure_dir(directory):
    """Ensure directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_scenes():
    """Generate video scenes by matching transcripts with clips"""
    # Ensure output directory exists
    output_dir = "Scenes"
    ensure_dir(output_dir)
    
    # Check for API key
    api_key = check_api_key()
    if not api_key:
        print("WARNING: OpenAI API key not found. Will fall back to basic matching.")
    
    # Read CSV data
    transcripts_df = pd.read_csv("transcripts_data.csv")
    clips_df = pd.read_csv("clips_data.csv")
    
    # Track which clips have been used
    used_clip_ids = set()
    
    # Process each transcript
    for index, transcript in transcripts_df.iterrows():
        transcript_id = transcript['id']
        transcript_length = float(transcript['length'])
        audio_file = transcript['audio_file']
        transcript_file = transcript['transcript_file']
        transcript_keywords = transcript['keywords']
        
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
        
        # Find matching clips using OpenAI to find semantic matches
        selected_clips = []
        current_length = 0
        remaining_clips = clips_df[~clips_df['id'].isin(used_clip_ids)].copy()
        
        if api_key and transcript_content:
            # Build a list of available clips with their keywords for the AI to choose from
            clips_list = []
            for _, clip in remaining_clips.iterrows():
                clips_list.append({
                    "id": clip['id'],
                    "keywords": clip['keywords'],
                    "length": float(clip['length'])
                })
            
            # Create prompt for OpenAI to match clips to transcript
            prompt = f"""
I need to match video clips to an audio transcript for a documentary scene. 
The transcript is about: "{transcript_content[:500]}..."

Keywords from transcript: {transcript_keywords}

I need to select clips that visually match this content with a total duration close to {transcript_length} seconds.
Available clips (ID, keywords, length in seconds):
{clips_list[:30]}  # Limiting to first 30 clips to avoid token limits

Select the best matching clips that total approximately {transcript_length} seconds.
Return a JSON array with just the clip IDs in your preferred order, like:
["clip-id-1", "clip-id-2", "clip-id-3"]
"""
            try:
                # Query OpenAI for clip selection
                response = query_openai(prompt, model="gpt-3.5-turbo")
                
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
                                # If we have enough clips, break
                                if current_length >= transcript_length * 0.95:
                                    break
                    except json.JSONDecodeError:
                        print("Could not parse AI response as JSON, falling back to basic matching")
            except Exception as e:
                print(f"Error using OpenAI for clip matching: {e}")
        
        # If we don't have enough clips yet (from AI or if AI failed), use basic matching
        if current_length < transcript_length * 0.8:
            print("Using basic matching to find additional clips")
            
            # Sort clips to ensure consistent selection
            sorted_clips = remaining_clips.sort_values(by='id')
            
            for _, clip in sorted_clips.iterrows():
                # Skip clips that have already been used
                if clip['id'] in used_clip_ids:
                    continue
                    
                # Add clip length check
                clip_length = float(clip['length'])
                
                # Skip clips that would exceed the target length
                if current_length + clip_length > transcript_length:
                    continue
                    
                selected_clips.append(clip)
                used_clip_ids.add(clip['id'])  # Mark this clip as used
                current_length += clip_length
                
                # If we have enough clips, break
                if current_length >= transcript_length * 0.95:  # Allow slight underrun
                    break
        
        if not selected_clips:
            print(f"No suitable unused clips found for transcript {transcript_id}")
            continue
            
        print(f"Selected {len(selected_clips)} clips with total length {current_length}s")
        
        # Combine clips with audio
        output_file = os.path.join(output_dir, f"{order_number}_scene_{transcript_id}.mp4")
        combine_clips_with_audio(selected_clips, audio_file, output_file)
        
        print(f"Created scene: {output_file}")

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
    generate_scenes()
