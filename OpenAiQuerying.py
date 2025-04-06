import os
import argparse
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

def query_openai(prompt, model="gpt-4o-mini", api_key=None):
    """
    Query the OpenAI API with the given prompt and return the response.
    
    Args:
        prompt (str): The text prompt to send to the API
        model (str): The OpenAI model to use (default: "gpt-4o-mini")
        api_key (str): OpenAI API key (will use environment variable if not provided)
    
    Returns:
        str: The text response from the API
    """
    # Create a client instance with the API key
    client = OpenAI(api_key=api_key)
    
    try:
        # Make the API request
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
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
    response = query_openai(prompt, model=args.model, api_key=args.api_key)
    
    # Print the response
    if response:
        print("\nAPI Response:")
        print(response)

if __name__ == "__main__":
    main()
