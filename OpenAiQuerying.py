import os
import argparse
import base64
from dotenv import load_dotenv
from openai import OpenAI
import time
import logging
from Models import ModelCategories
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Token rate limiting configuration
TOKEN_RATE_LIMITS = {
    "gpt-4o": 30000,      # tokens per minute
    "gpt-4o-mini": 200000,  # tokens per minute
    "default": 30000       # default for other models
}
TOKEN_WINDOW = 60  # seconds
token_usage = []  # List of (timestamp, tokens) pairs

def calculate_sleep_time(tokens_used, model=None):
    """
    Calculate the required sleep time based on token usage to respect rate limits.
    
    Args:
        tokens_used (int): Number of tokens used in the current request
        model (str): The model being used, to determine rate limits
        
    Returns:
        float: Number of seconds to sleep
    """
    global token_usage
    current_time = datetime.now()
    
    # Determine the appropriate rate limit based on the model
    rate_limit = TOKEN_RATE_LIMITS.get(model, TOKEN_RATE_LIMITS["default"])
    logger.info(f"Using rate limit of {rate_limit} tokens per minute for model {model}")
    
    logger.info(f"Calculating sleep time for {tokens_used} tokens used")
    
    # Remove old entries outside the time window
    token_usage = [(ts, t) for ts, t in token_usage 
                  if current_time - ts < timedelta(seconds=TOKEN_WINDOW)]
    
    logger.info(f"Current token usage window contains {len(token_usage)} entries")
    
    # Add current usage
    token_usage.append((current_time, tokens_used))
    
    # Calculate total tokens used in the window
    total_tokens = sum(t for _, t in token_usage)
    logger.info(f"Total tokens used in window: {total_tokens}/{rate_limit}")
    
    # If we're under the limit, no need to sleep
    if total_tokens <= rate_limit:
        logger.info("Token usage within limits, no sleep required")
        return 0
    
    # Calculate how much we exceeded the limit
    excess_tokens = total_tokens - rate_limit
    logger.info(f"Exceeding rate limit by {excess_tokens} tokens")
    
    # Calculate sleep time needed to get back under the limit
    # We distribute the excess tokens over the remaining time in the window
    time_elapsed = (current_time - token_usage[0][0]).total_seconds()
    remaining_time = max(0, TOKEN_WINDOW - time_elapsed)
    
    if remaining_time == 0:
        logger.info("Window has expired, no sleep required")
        return 0
    
    # Calculate sleep time needed to process excess tokens
    sleep_time = (excess_tokens / rate_limit) * TOKEN_WINDOW
    logger.info(f"Sleep time calculated: {sleep_time:.2f} seconds")
    
    return sleep_time

def check_api_key():
    """Check if the OPENAI_API_KEY environment variable is set and return its value"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        # Show first few and last few characters for verification
        visible_part = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
        print(f"[OK] OPENAI_API_KEY is set: {visible_part}")
        return api_key
    else:
        print("[ERROR] OPENAI_API_KEY is not set in environment variables or .env file")
        return None

def encode_image(image_path):
    """
    Encode an image file to base64 string.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64 encoded string of the image
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def query_openai(prompt, model=ModelCategories.getDefaultModel(), api_key=None, image_path=None):
    """
    Query the OpenAI API with the given prompt and return the response.
    
    Args:
        prompt (str): The text prompt to send to the API
        model (str): The OpenAI model to use (default: from ModelCategories)
        api_key (str): OpenAI API key (will use environment variable if not provided)
        image_path (str): Optional path to an image file to include in the query
    
    Returns:
        str: The text response from the API
    """
    # Create a client instance with the API key
    client = OpenAI(api_key=api_key)
    
    try:
        # Prepare messages based on whether an image is included
        if image_path and os.path.exists(image_path):
            # Vision-capable models
            if not model.startswith(("gpt-4-vision", "gpt-4o")):
                print(f"Warning: Model {model} may not support image inputs. Consider using gpt-4o or gpt-4-vision.")
            
            base64_image = encode_image(image_path)
            if base64_image:
                # Get file extension for the content type
                _, ext = os.path.splitext(image_path)
                content_type = f"image/{ext[1:]}" if ext else "image/jpeg"
                
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            else:
                print("Failed to encode image. Proceeding with text-only query.")
                messages = [{"role": "user", "content": prompt}]
        else:
            # Text-only query
            messages = [{"role": "user", "content": prompt}]
        
        # Make the API request
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7
        )

        # Calculate tokens used (prompt + completion)
        tokens_used = response.usage.total_tokens
        
        # Calculate and apply dynamic sleep time based on the current model
        sleep_time = calculate_sleep_time(tokens_used, model)
        if sleep_time > 0:
            print(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds to respect token limits")
            time.sleep(sleep_time)
        
        # Return the response text
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error making API request: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Query the OpenAI API with text input")
    parser.add_argument("--prompt", type=str, help="Text prompt to send to the API")
    parser.add_argument("--model", type=str, default=ModelCategories.getDefaultModel(), help="OpenAI model to use")
    parser.add_argument("--api_key", type=str, help="OpenAI API key (optional if set as environment variable)")
    parser.add_argument("--file", type=str, help="File containing prompt text (optional)")
    parser.add_argument("--image", type=str, help="Path to an image file to include in the query")
    parser.add_argument("--check", action="store_true", help="Check if OPENAI_API_KEY is set")
    parser.add_argument("--env", type=str, help="Path to .env file (default is .env in current directory)")
    
    args = parser.parse_args()
    
    # Load from specified env file if provided
    if args.env:
        if os.path.exists(args.env):
            load_dotenv(args.env)
            print(f"Loaded environment from: {args.env}")
        else:
            print(f"Warning: Specified .env file not found: {args.env}")
    
    # Check if API key is set if requested
    if args.check:
        check_api_key()
        return
    
    # Get prompt from file or command line
    prompt = args.prompt
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                prompt = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    
    if not prompt:
        prompt = input("Enter your prompt: ")
    
    # Query the API
    response = query_openai(prompt, model=args.model, api_key=args.api_key, image_path=args.image)
    
    # Print the response
    if response:
        print("\nAPI Response:")
        print(response)

if __name__ == "__main__":
    main()
