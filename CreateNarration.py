import os
import sys
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from pathlib import Path

class CreateNarration:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize ElevenLabs API key
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            print("Error: ELEVENLABS_API_KEY not found in environment variables.")
            self.client = None
        else:
            # Initialize the ElevenLabs client
            self.client = ElevenLabs(api_key=self.api_key)
        
        # Define paths
        self.transcript_folder = Path("Transcript")
        self.audio_folder = Path("Audio")
        
        # Create Audio folder if it doesn't exist
        if not self.audio_folder.exists():
            self.audio_folder.mkdir(exist_ok=True)
            print(f"Created Audio folder at {self.audio_folder.absolute()}")
    
    def process_transcripts(self):
        if not self.client:
            print("ElevenLabs client not initialized. Check your API key.")
            return False
            
        # Get all txt files from the Transcript folder
        transcript_files = list(self.transcript_folder.glob("*.txt"))
        
        if not transcript_files:
            print("No transcript files found in the Transcript folder.")
            return False
        
        print(f"Found {len(transcript_files)} transcript file(s) to process.")
        
        # Process each transcript file
        for transcript_file in transcript_files:
            file_stem = transcript_file.stem
            output_file = self.audio_folder / f"{file_stem}.mp3"
            
            # Skip if output file already exists
            if output_file.exists():
                print(f"Audio file {output_file} already exists. Skipping.")
                continue
            
            print(f"Processing {transcript_file.name}...")
            
            # Read transcript content
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript_text = f.read()
            
            # Generate audio using ElevenLabs
            try:
                # Get available voices
                voices = self.client.voices.get_all()
                voice_id = None
                
                # Try to find Daniel voice
                for voice in voices.voices:
                    if voice.name.lower() == "daniel":
                        voice_id = voice.voice_id
                        break
                
                if not voice_id:
                    # If Daniel not found, use the first available voice
                    voice_id = voices.voices[0].voice_id if voices.voices else None
                    
                if not voice_id:
                    raise Exception("No voices available in your ElevenLabs account")
                
                # Generate audio
                audio = self.client.text_to_speech.convert(
                    text=transcript_text,
                    voice_id=voice_id,
                    model_id="eleven_monolingual_v1"
                )
                
                # Save the audio to a file
                with open(str(output_file), "wb") as f:
                    # Handle the generator by consuming it
                    for chunk in audio:
                        f.write(chunk)
                
                print(f"Successfully saved audio to {output_file}")
                
            except Exception as e:
                print(f"Error processing {transcript_file.name}: {str(e)}")
        
        print("All transcript files processed.")
        return True
    
    def process_single_transcript(self, transcript_file_path):
        if not self.client:
            print("ElevenLabs client not initialized. Check your API key.")
            return False
            
        transcript_file = Path(transcript_file_path)
        if not transcript_file.exists():
            print(f"Transcript file {transcript_file} not found.")
            return False
            
        file_stem = transcript_file.stem
        output_file = self.audio_folder / f"{file_stem}.mp3"
        
        print(f"Processing {transcript_file.name}...")
        
        # Read transcript content
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript_text = f.read()
        
        # Generate audio using ElevenLabs
        try:
            # Get available voices
            voices = self.client.voices.get_all()
            voice_id = None
            
            # Try to find Daniel voice
            for voice in voices.voices:
                if voice.name.lower() == "daniel":
                    voice_id = voice.voice_id
                    break
            
            if not voice_id:
                # If Daniel not found, use the first available voice
                voice_id = voices.voices[0].voice_id if voices.voices else None
                
            if not voice_id:
                raise Exception("No voices available in your ElevenLabs account")
            
            # Generate audio
            audio = self.client.text_to_speech.convert(
                text=transcript_text,
                voice_id=voice_id,
                model_id="eleven_monolingual_v1"
            )
            
            # Save the audio to a file
            with open(str(output_file), "wb") as f:
                # Handle the generator by consuming it
                for chunk in audio:
                    f.write(chunk)
            
            print(f"Successfully saved audio to {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error processing {transcript_file.name}: {str(e)}")
            return False

def main():
    narrator = CreateNarration()
    narrator.process_transcripts()

if __name__ == "__main__":
    main()
