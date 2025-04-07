import os
import argparse
import base64
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

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

def query_openai(prompt, model="gpt-4o-mini", api_key=None, image_path=None):
    """
    Query the OpenAI API with the given prompt and return the response.
    
    Args:
        prompt (str): The text prompt to send to the API
        model (str): The OpenAI model to use (default: "gpt-4o-mini")
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
        
        # Return the response text
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error making API request: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Query the OpenAI API with text input")
    parser.add_argument("--prompt", type=str, help="Text prompt to send to the API")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo", help="OpenAI model to use")
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
