import os
import ProjectManager

# Global project manager instance
_project_manager = ProjectManager.get_project_manager()

def get_project_manager():
    """Get the global project manager instance"""
    return _project_manager

def set_current_project(project_name):
    """Set the current project"""
    _project_manager.load_project(project_name)

def get_current_project():
    """Get the current project name"""
    return _project_manager.current_project

def get_transcript_dir():
    """Get the path to the Transcript directory"""
    if _project_manager.current_project:
        return _project_manager.get_project_path("Transcript")
    return "Transcript"

def get_clips_dir():
    """Get the path to the Clips directory"""
    if _project_manager.current_project:
        return _project_manager.get_project_path("Clips")
    return "Clips"

def get_scenes_dir():
    """Get the path to the Scenes directory"""
    if _project_manager.current_project:
        return _project_manager.get_project_path("Scenes")
    return "Scenes"

def get_audio_dir():
    """Get the path to the Audio directory"""
    if _project_manager.current_project:
        return _project_manager.get_project_path("Audio")
    return "Audio"

def get_raw_video_dir():
    """Get the path to the RawVideo directory"""
    if _project_manager.current_project:
        return _project_manager.get_project_path("RawVideo")
    return "RawVideo"

def get_output_dir():
    """Get the path to the Output directory"""
    if _project_manager.current_project:
        return _project_manager.get_project_path("Output")
    return "Output"

def get_research_dir():
    """Get the path to the Research directory"""
    if _project_manager.current_project:
        return _project_manager.get_project_path("Research")
    return "Research"

def get_clips_data_path():
    """Get the path to the clips_data.csv file"""
    if _project_manager.current_project:
        return os.path.join(_project_manager.get_project_path(), "clips_data.csv")
    return "clips_data.csv"

def get_transcripts_data_path():
    """Get the path to the transcripts_data.csv file"""
    if _project_manager.current_project:
        return os.path.join(_project_manager.get_project_path(), "transcripts_data.csv")
    return "transcripts_data.csv"

def get_project_path(subfolder=None):
    """Get the path to the current project or a subfolder within it"""
    if _project_manager.current_project:
        if subfolder:
            return _project_manager.get_project_path(subfolder)
        return _project_manager.get_project_path()
    return subfolder if subfolder else "."

def ensure_directory(directory):
    """Ensure a directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    return directory 