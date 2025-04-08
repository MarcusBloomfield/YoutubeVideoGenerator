"""
This module contains centralized model references used throughout the project.
All model names should be referenced from here to maintain consistency.
"""

# Default models for different tasks
DEFAULT_MODEL = "gpt-4o-mini"  # Default model for most operations
RESEARCH_MODEL = "gpt-4o-mini"      # Model used for research-related tasks
SCENE_GENERATION_MODEL = "gpt-4o-mini"  # Model used for scene generation
EXPAND_TRANSCRIPT_MODEL = "gpt-4o"  # Model used for expanding transcripts
WRITE_TRANSCRIPT_MODEL = "gpt-4o"  # Model used for writing transcripts
PURIFY_TRANSCRIPT_MODEL = "gpt-4o"  # Model used for purifying transcripts

# Model categories for different use cases
class ModelCategories:
    """Categories of models for different use cases"""
    
    @staticmethod
    def getDefaultModel():
        """Returns the default model for general operations"""
        return DEFAULT_MODEL
        
    @staticmethod
    def getResearchModel():
        """Returns the model used for research-related tasks"""
        return RESEARCH_MODEL
        
    @staticmethod
    def getSceneGenerationModel():
        """Returns the model used for scene generation"""
        return SCENE_GENERATION_MODEL 
    
    @staticmethod
    def getWriteTranscriptModel():
        """Returns the model used for writing transcripts"""
        return WRITE_TRANSCRIPT_MODEL
    
    @staticmethod
    def getPurifyTranscriptModel():
        """Returns the model used for purifying transcripts"""
        return PURIFY_TRANSCRIPT_MODEL

    @staticmethod
    def getExpandTranscriptModel():
        """Returns the model used for expanding transcripts"""
        return EXPAND_TRANSCRIPT_MODEL
