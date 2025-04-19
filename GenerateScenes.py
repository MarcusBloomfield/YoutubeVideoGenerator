import os
import csv
import subprocess
import pandas as pd
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from OpenAiQuerying import query_openai, check_api_key
import random
import shutil
from Prompts import CLIP_MATCHING_PROMPT, SCENE_GENERATION_PROMPT
from Models import ModelCategories
import numpy as np
import sys
import json
from datetime import datetime
import logging

# Configure logging for this module
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

class GenerateScenes:
    """Class for generating video scenes by matching transcripts with clips"""
    
    # Maximum number of clips to score before AI selection
    MAX_AI_CLIPS = 1000
    # Additional seconds to add beyond transcript length for buffer
    ADDITIONAL_TIME_BUFFER = 3

    MAX_CLIP_LENGTH = 5
    
    def __init__(self):
        """Initialize the scene generator"""
        pass
        
    @staticmethod
    def ensure_dir(directory):
        """Ensure directory exists, create if it doesn't"""
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    @staticmethod
    def parse_keywords(raw_keywords):
        """Parse raw clip keywords into a list of cleaned, lowercase keywords"""
        if pd.isna(raw_keywords):
            return []
        if not isinstance(raw_keywords, str):
            raw_keywords = str(raw_keywords)
        return [keyword.strip().lower() for keyword in raw_keywords.split(",") if keyword.strip()]
   
    def generate_scenes_by_matching(self):
        """Generate video scenes by matching transcripts with clips"""
        # Prepare output and archive directories
        output_dir = "Scenes"
        self.ensure_dir(output_dir)
        transcript_archive_dir = os.path.join("Transcript", "old")
        self.ensure_dir(transcript_archive_dir)

        # Verify API key
        if not check_api_key():
            logger.error("OpenAI API key not found. Cannot proceed with scene generation.")
            return
        
        # Load data
        transcripts_df, clips_df = self.load_data()
        # Load previously used clip IDs from CSV for persistence
        previous_used_clip_ids = self.load_previous_used_clip_ids()
        used_clip_ids = set(previous_used_clip_ids)
        
        # Process each transcript entry
        for index, transcript in transcripts_df.iterrows():
            self.process_transcript(transcript, index, clips_df, output_dir, transcript_archive_dir, used_clip_ids)
        
        # Summary
        logger.info("Generation complete. Used %s unique clips across all scenes.", len(used_clip_ids))
        # Save updated used clip IDs to CSV
        self.save_used_clip_ids(used_clip_ids, previous_used_clip_ids)

    def load_data(self):
        """Load transcripts and clips data from CSV files."""
        transcripts_df = pd.read_csv("transcripts_data.csv")
        clips_df = pd.read_csv("clips_data.csv")
        return transcripts_df, clips_df

    def load_previous_used_clip_ids(self):
        """Load previously used clip IDs from CSV file."""
        used_ids = set()
        if os.path.exists("used_clip_ids.csv"):
            try:
                with open("used_clip_ids.csv", 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    next(reader, None)  # Skip header if present
                    for row in reader:
                        if row:
                            used_ids.add(row[0])
            except Exception as e:
                logger.error("Error reading used_clip_ids.csv: %s", e)
        return used_ids

    def save_used_clip_ids(self, all_used_ids, previous_ids):
        """Append new used clip IDs to CSV file."""
        new_ids = [cid for cid in all_used_ids if cid not in previous_ids]
        if not new_ids:
            logger.info("No new used clip IDs to append to used_clip_ids.csv")
            return
        file_existed = os.path.exists("used_clip_ids.csv")
        try:
            with open("used_clip_ids.csv", 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if not file_existed:
                    writer.writerow(["id"])
                for cid in new_ids:
                    writer.writerow([cid])
            logger.info("Appended %s new used clip IDs to used_clip_ids.csv", len(new_ids))
        except Exception as e:
            logger.error("Error writing to used_clip_ids.csv: %s", e)

    def extract_order_number(self, audio_file, index):
        """Extract order number from audio filename or fallback to index."""
        order_number = "000"
        if "_" in os.path.basename(audio_file):
            try:
                filename = os.path.basename(audio_file)
                order_number = filename.split("_")[0]
            except Exception:
                order_number = f"{index+1:03d}"
        return order_number

    def read_transcript_content(self, transcript_file):
        """Read transcript file content with UTF-8 encoding, logging errors."""
        if os.path.exists(transcript_file):
            try:
                with open(transcript_file, 'r', encoding='utf-8') as file:
                    return file.read()
            except Exception as e:
                logger.error("Error reading transcript file %s: %s", transcript_file, e)
                return ""
        logger.warning("Transcript file not found: %s", transcript_file)
        return ""

    def filter_remaining_clips(self, clips_df, used_clip_ids):
        """Filter out clips that have already been used."""
        remaining = clips_df[~clips_df['id'].isin(used_clip_ids)].copy()
        if remaining.empty:
            logger.warning("All clips have been used. Consider adding more content.")
        return remaining

    def build_clips_list(self, remaining_clips):
        """Build list of clip dictionaries for scoring."""
        clips_list = []
        for _, clip in remaining_clips.iterrows():
            clips_list.append({
                'id': clip['id'],
                'keywords': clip['keywords'],
                'length': float(clip['length'])
            })
        return clips_list

    def score_clips_by_keywords(self, clips_list, transcript_text_lower):
        """Score clips based on keyword matches in transcript."""
        for clip in clips_list:
            raw = clip['keywords']
            logger.debug("Raw keywords for clip %s: %r", clip['id'], raw)
            keywords = self.parse_keywords(raw)
            logger.debug("Parsed keywords for clip %s: %s", clip['id'], keywords)
            clip['match_score'] = sum(1 for kw in keywords if kw in transcript_text_lower)
        # Sort descending by match score
        clips_list.sort(key=lambda c: c['match_score'], reverse=True)
        return clips_list

    def select_top_clips(self, clips_list):
        """Select top clips for AI evaluation based on match scores."""
        selected = clips_list[:self.MAX_AI_CLIPS]
        logger.info("Selected top %s clips for AI: %s", len(selected), [(c['id'], c['match_score']) for c in selected])
        return selected

    def select_random_clips(self, clips_list, remaining_clips):
        """Fallback to random selection when no keyword matches."""
        if all(c['match_score'] == 0 for c in clips_list):
            logger.warning("No keyword matches found; falling back to random selection.")
            random.shuffle(clips_list)
        return clips_list[:self.MAX_AI_CLIPS]

    def create_matching_prompt(self, transcript_content, transcript_length, clips_list):
        """Create the OpenAI prompt to match clips to transcript."""
        return CLIP_MATCHING_PROMPT.format(
            transcript_content=transcript_content,
            transcript_length=transcript_length,
            clips_list=clips_list
        )

    def select_clips_with_ai(self, prompt, remaining_clips, used_clip_ids, transcript_length):
        """Query OpenAI and parse selected clip IDs until required audio length + 1 second is met."""
        target_length = transcript_length + 1
        logger.debug("Target length for clip selection: %ss", target_length)
        selected_clips = []
        current_length = 0
        import re
        while current_length < target_length:
            try:
                response = query_openai(prompt, model=ModelCategories.getSceneGenerationModel())
                match = re.search(r'\[.*?\]', response, re.DOTALL)
                if not match:
                    logger.warning("No clip IDs found in AI response; stopping selection")
                    break
                ids = json.loads(match.group(0))
                clips_added_this_round = 0
                for cid in ids:
                    if cid in remaining_clips['id'].values and cid not in used_clip_ids:
                        clip_row = remaining_clips[remaining_clips['id'] == cid].iloc[0]
                        selected_clips.append(clip_row)
                        used_clip_ids.add(cid)
                        length_added = float(clip_row['length'])
                        if (length_added > self.MAX_CLIP_LENGTH):
                            length_added = self.MAX_CLIP_LENGTH
                        current_length += length_added

                        clips_added_this_round += 1
                        logger.debug("Added clip %s (length %ss); updated length %ss", cid, length_added, current_length)
                        if current_length >= target_length:
                            logger.debug("Reached target length %ss", current_length)
                            break
                if clips_added_this_round == 0:
                    logger.warning("No new valid clips were added; stopping further selection")
                    break
            except Exception as e:
                logger.error("Error using OpenAI for clip selection: %s", e, exc_info=True)
                break
        return selected_clips, current_length

    def process_transcript(self, transcript, index, clips_df, output_dir, archive_dir, used_clip_ids):
        """Process a single transcript row: select clips and create scene."""
        transcript_id = transcript['id']
        transcript_length = float(transcript['length'])
        audio_file = transcript['audio_file']
        transcript_file = transcript['transcript_file']
        order_number = self.extract_order_number(audio_file, index)
        logger.info("Processing transcript %s with target length %ss", transcript_id, transcript_length)

        # Read content and archive if needed
        content = self.read_transcript_content(transcript_file)
        if not content:
            return

        # Filter and score clips
        remaining = self.filter_remaining_clips(clips_df, used_clip_ids)
        if remaining.empty:
            return
        clips_list = self.build_clips_list(remaining)
        transcript_text_lower = content.lower()
        scored = self.score_clips_by_keywords(clips_list, transcript_text_lower)
        top = self.select_top_clips(scored)
        selected_for_ai = self.select_random_clips(top, remaining)

        # AI-based selection
        prompt = self.create_matching_prompt(content, transcript_length, selected_for_ai)
        selected_clips, total_length = self.select_clips_with_ai(prompt, remaining, used_clip_ids, transcript_length)

        if not selected_clips:
            logger.warning("No suitable clips found for transcript %s", transcript_id)
            return
        if total_length <= transcript_length:
            logger.warning("Could not exceed transcript length for %s; using available clips.", transcript_id)

        logger.info("Selected %s clips with total length %ss for transcript %s", len(selected_clips), total_length, transcript_id)
        output_file = os.path.join(output_dir, f"{order_number}_scene_{transcript_id}.mp4")
        success = self.combine_clips_with_audio(selected_clips, audio_file, output_file)
        if success:
            logger.info("Created scene: %s", output_file)

    def trim_video(self, video_path):
        """Load video from the given path, trim to MAX_CLIP_LENGTH if necessary, remove audio, and return the muted clip."""
        logger.info("Loading clip from: %s", video_path)
        video_raw = VideoFileClip(video_path)
        logger.debug("Original duration of clip %s: %ss", video_path, video_raw.duration)
        if video_raw.duration > self.MAX_CLIP_LENGTH:
            trimmed_clip = video_raw.subclip(0, self.MAX_CLIP_LENGTH)
            logger.info("Trimmed clip %s to maximum of %ss (actual %ss)", video_path, self.MAX_CLIP_LENGTH, trimmed_clip.duration)
        else:
            trimmed_clip = video_raw
        # Mute the video to avoid audio overlap
        return trimmed_clip.without_audio()

    def combine_clips_with_audio(self, clips, audio_file, output_file):
        """Combine video clips with audio file into a single MP4"""
        try:
            # Load all video clips
            video_clips = []
            for clip in clips:
                video_path = clip['filelocation']
                # Trim and mute the video clip using trim_video helper
                video_muted = self.trim_video(video_path)
                video_clips.append(video_muted)
            
            # Concatenate video clips
            final_clip = concatenate_videoclips(video_clips)
            
            # Load the audio
            logger.info("Adding audio from: %s", audio_file)
            audio = AudioFileClip(audio_file)
            
            # Verify audio loaded correctly
            if audio is None:
                print(f"Error: Audio could not be loaded from {audio_file}")
                return False
            
            # Process audio to remove dead air longer than 1 second
            logger.info("Analyzing audio for long silent periods...")
            
            logger.info("Audio duration after silence trimming: %ss, Video duration: %ss", audio.duration, final_clip.duration)
            
            # Ensure audio doesn't exceed video duration
            if audio.duration > final_clip.duration:
                audio = audio.subclip(0, final_clip.duration)
            # Ensure video doesn't exceed audio duration (no visuals without audio)
            elif final_clip.duration > audio.duration:
                final_clip = final_clip.subclip(0, audio.duration + 1)
                print(f"Trimmed video to match audio duration: {audio.duration}s")
            
            # Create final clip with audio
            final_clip_with_audio = final_clip.set_audio(audio)
            
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
            
            logger.info("Successfully created: %s", output_file)
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
