import os
import datetime
import logging
from dotenv import load_dotenv
import OpenAiQuerying
from Models import ModelCategories

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

def read_topics_file():
    """Read existing topics from Topics.txt file"""
    topics = []
    if os.path.exists("Topics.txt"):
        with open("Topics.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    topics.append(line)
    return topics

def save_topic(theme, topic):
    """Save a generated topic to the Topics.txt file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create file if it doesn't exist
    if not os.path.exists("Topics.txt"):
        with open("Topics.txt", "w", encoding="utf-8") as f:
            f.write("# Generated Topics for YouTube Video Generator\n\n")
    
    # Append the new topic
    with open("Topics.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {theme}: {topic}\n")

def generate_topic_idea(theme, model=None):
    """
    Generate a specific video topic idea based on a broader theme.
    
    Args:
        theme: The general theme or category (e.g., "World War II", "Space Exploration")
        model: The OpenAI model to use (optional)
        
    Returns:
        str: A specific topic idea for video generation
    """
    logger.info(f"Generating topic idea for theme: {theme}")
    
    # Read existing topics to avoid duplicates
    existing_topics = read_topics_file()
    if existing_topics:
        logger.info(f"Found {len(existing_topics)} existing topics in Topics.txt")
    
    # Create a prompt for OpenAI that includes previous topics to avoid
    if existing_topics:
        # Extract just the topic names from the last 10 entries
        recent_topics = []
        for line in existing_topics[-10:]:
            if ":" in line:
                topic_part = line.split(":", 1)[1].strip()
                recent_topics.append(topic_part)
        
        if recent_topics:
            topics_to_avoid = ", ".join([f'"{t}"' for t in recent_topics])
            prompt = f"""Generate a specific, engaging video topic related to "{theme}".
Return ONLY the topic title (1-4 words), without quotes or additional text or any other type of formatting.

IMPORTANT: Do NOT generate any of these previously used topics: {topics_to_avoid}"""
        else:
            prompt = f"""Generate a specific, engaging video topic related to "{theme}".
Return ONLY the topic title (1-4 words), without quotes or additional text or any other type of formatting."""
    else:
        prompt = f"""Generate a specific, engaging video topic related to "{theme}".
Return ONLY the topic title (1-4 words), without quotes or additional text or any other type of formatting."""
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OpenAI API key not set")
        return None
    
    # Query OpenAI for a topic idea
    try:
        # Use a more concise model for this simple task or use the provided one
        if model is None:
            model = ModelCategories.getDefaultModel()
            
        logger.info(f"Using model: {model} for topic generation")
        topic_idea = OpenAiQuerying.query_openai(prompt, model=model)
        
        if not topic_idea:
            logger.error("Failed to generate topic idea")
            return None
        
        # Clean up the response
        topic_idea = topic_idea.strip()
        logger.info(f"Generated topic idea: {topic_idea}")
        
        # Save to file
        save_topic(theme, topic_idea)
        logger.info("Topic saved to Topics.txt")
        
        return topic_idea
        
    except Exception as e:
        logger.error(f"Error generating topic idea: {str(e)}")
        return None

if __name__ == "__main__":
    # Load environment variables (for API key)
    load_dotenv()
    
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate a video topic idea based on a theme")
    parser.add_argument("theme", type=str, help="General theme to generate a topic from")
    parser.add_argument("--model", type=str, help="OpenAI model to use (optional)")
    args = parser.parse_args()
    
    topic = generate_topic_idea(args.theme, model=args.model)
    if topic:
        print(f"\nGenerated topic: {topic}")
    else:
        print("Error: Failed to generate a topic.") 