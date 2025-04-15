import os
import csv
import subprocess
import pandas as pd
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from OpenAiQuerying import query_openai, check_api_key
import random
import shutil
from Prompts import CLIP_MATCHING_PROMPT, SCENE_GENERATION_PROMPT
from Models import ModelCategories
import numpy as np
import sys
import json
from datetime import datetime

class GenerateScenes:
    """Class for generating video scenes by matching transcripts with clips"""
    
    def __init__(self):
        """Initialize the scene generator"""
        pass
        
    @staticmethod
    def ensure_dir(directory):
        """Ensure directory exists, create if it doesn't"""
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    @staticmethod
    def detect_and_trim_silence(audio, min_volume=0.1, max_silence_duration=1.0):
        """Detect and trim silent periods longer than max_silence_duration seconds"""
        # Get audio array and sampling rate
        audio_array = audio.to_soundarray()
        fps = audio.fps
        
        # Calculate volume at each point (combine channels if stereo)
        if len(audio_array.shape) > 1 and audio_array.shape[1] > 1:
            volume = np.sqrt(np.mean(audio_array**2, axis=1))
        else:
            volume = np.abs(audio_array)
            
        # Detect silent regions (below min_volume)
        is_silent = volume < min_volume
        
        # Find silence boundaries
        silence_start = np.where(np.concatenate(([False], is_silent[:-1] == False, [False])) & 
                                np.concatenate(([False], is_silent[1:] == True, [False])))[0]
        silence_end = np.where(np.concatenate(([False], is_silent[:-1] == True, [False])) & 
                                np.concatenate(([False], is_silent[1:] == False, [False])))[0]
        
        # Convert frame indices to time
        silence_start_time = silence_start / fps
        silence_end_time = silence_end / fps
        
        # Calculate silence durations
        silence_durations = silence_end_time - silence_start_time
        
        # Identify long silences to trim
        long_silences = []
        for i in range(len(silence_start_time)):
            if silence_durations[i] > max_silence_duration:
                # Keep max_silence_duration/2 at the beginning and end of each silence
                half_silence = max_silence_duration / 2
                # If silence is longer than allowed, add to trim list
                long_silences.append((silence_start_time[i] + half_silence, 
                                     silence_end_time[i] - half_silence))
        
        # If no long silences found, return original audio
        if not long_silences:
            return audio
            
        # Trim the audio by creating subclips and concatenating
        if long_silences:
            print(f"Found {len(long_silences)} silence periods longer than {max_silence_duration}s")
            
            # Create list of audio segments to keep
            subclips = []
            last_end = 0
            
            for start, end in long_silences:
                # Add segment before silence
                if start > last_end:
                    subclips.append(audio.subclip(last_end, start))
                last_end = end
                
            # Add final segment after last silence
            if last_end < audio.duration:
                subclips.append(audio.subclip(last_end, audio.duration))
                
            # Concatenate all non-silence segments
            if subclips:
                return concatenate_audioclips(subclips)
            else:
                return audio
        
        return audio

    def generate_scenes_by_matching(self):
        """Generate video scenes by matching transcripts with clips"""
        # Ensure output directory exists
        output_dir = "Scenes"
        self.ensure_dir(output_dir)
        
        # Ensure transcript archive directory exists
        transcript_archive_dir = os.path.join("Transcript", "old")
        self.ensure_dir(transcript_archive_dir)
        
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
            
            # Randomly select 100 clips (or all if less than 100 available)
            num_clips_to_select = min(100, len(clips_list))
            clips_list = random.sample(clips_list, num_clips_to_select)
            print(f"[INFO] Randomly selected {num_clips_to_select} clips from {len(remaining_clips)} available clips")
            
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
            success = self.combine_clips_with_audio(selected_clips, audio_file, output_file)
            
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

    def combine_clips_with_audio(self, clips, audio_file, output_file):
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
            
            # Process audio to remove dead air longer than 1 second
            print("Analyzing audio for long silent periods...")
            audio = self.detect_and_trim_silence(audio, max_silence_duration=1.0)
            
            print(f"Audio duration after silence trimming: {audio.duration}, Video duration: {final_clip.duration}")
            
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

    def main(self):
        """Main entry point for scene generation"""
        return self.generate_scenes_by_matching()

if __name__ == "__main__":
    generator = GenerateScenes()
    generator.main()
