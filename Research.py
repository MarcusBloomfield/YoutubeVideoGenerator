import os
import requests
from bs4 import BeautifulSoup
import re
import datetime
import argparse
from urllib.parse import urlparse
from OpenAiQuerying import query_openai, check_api_key
import time
from Prompts import RESEARCH_EXTRACT_INFO_PROMPT, RESEARCH_SUMMARY_PROMPT, RESEARCH_EXPANSION_PROMPT
from Models import ModelCategories

def create_research_folder():
    """Create a Research folder if it doesn't exist"""
    research_folder = "Research"
    if not os.path.exists(research_folder):
        os.makedirs(research_folder)
        print(f"Created {research_folder} directory")
    return research_folder

def get_webpage_content(url):
    """
    Fetch and parse content from a URL
    
    Args:
        url (str): The URL to fetch content from
        
    Returns:
        str: The extracted text content from the webpage
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up text (remove extra whitespace, etc.)
        text = re.sub(r'\s+', ' ', text).strip()
        
        print(f"Successfully fetched content from {url}")
        return text
    except Exception as e:
        print(f"Error fetching content from {url}: {e}")
        return ""

def extract_domain(url):
    """Extract the domain name from a URL"""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain

def extract_relevant_info(content, topic, url, existingResearch):
    """
    Use OpenAI to extract relevant information about the topic from the content
    
    Args:
        content (str): The webpage content
        topic (str): The research topic
        url (str): The source URL
        existingResearch (str): The past research on the topic
    Returns:
        str: Relevant information extracted from the content
    """
    # Truncate content if it's too long (to fit within token limits)
    max_content_length = 10000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "... [content truncated]"
    
    prompt = RESEARCH_EXTRACT_INFO_PROMPT.format(
        domain=extract_domain(url),
        topic=topic,
        content=content,
        existingResearch=existingResearch
    )
    
    response = query_openai(prompt, model="gpt-4o")
    
    if response and "NO_RELEVANT_INFO" not in response:
        return f"Source: {url}\n\n{response}\n\n"
    return ""

def research_topic(urls, topic):
    """
    Research a topic by extracting relevant information from a list of URLs
    
    Args:
        urls (list): List of URLs to extract information from
        topic (str): The research topic
        
    Returns:
        str: Path to the created or updated research file
    """
    research_folder = create_research_folder()
    
    # Create a valid filename from the topic
    filename = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
    research_file = os.path.join(research_folder, f"{filename}.txt")
    
    # Check if research file already exists
    existing_research = ""
    is_update = os.path.exists(research_file)
    
    if is_update:
        print(f"Research file for '{topic}' already exists. Reading existing content...")
        try:
            with open(research_file, 'r', encoding='utf-8') as f:
                existing_research = f.read()
            print(f"Successfully read existing research file.")
        except Exception as e:
            print(f"Error reading existing research file: {e}")
            existing_research = ""
    
    # Initialize new research content
    new_research = ""
    
    # Process new URLs
    for url in urls:
        print(f"Processing {url}")
        content = get_webpage_content(url)
        if content:
            relevant_info = extract_relevant_info(content, topic, url, existing_research)
            if relevant_info:
                new_research += relevant_info
                new_research += "-" * 30 + "\n\n"
    
    if not new_research:
        print("No new relevant information found.")
        if is_update:
            return research_file
    
    # Create expanded research using the prompt
    expansion_prompt = RESEARCH_EXPANSION_PROMPT.format(
        topic=topic,
        existing_research=existing_research,
        new_research=new_research
    )
    
    # Get the expanded research from OpenAI
    expanded_research = query_openai(expansion_prompt, model="gpt-4o")
    
    # Add a summary at the end using OpenAI
    summary_prompt = RESEARCH_SUMMARY_PROMPT.format(
        topic=topic,
        combined_research=expanded_research
    )
    
    summary = query_openai(summary_prompt, model="gpt-4o")
    
    # Add timestamp and format the final research
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_research = f"Research on: {topic}\n"
    final_research += f"Last Updated: {timestamp}\n"
    final_research += "=" * 50 + "\n\n"
    final_research += expanded_research.strip()
    final_research += "\n\nSUMMARY\n"
    final_research += "=" * 50 + "\n"
    final_research += summary
    
    # Save research to file
    with open(research_file, 'w', encoding='utf-8') as f:
        f.write(final_research)
    
    if is_update:
        print(f"Research file expanded and updated at {research_file}")
    else:
        print(f"New research saved to {research_file}")
    
    return research_file

def main():
    """Main function to run the research tool using command line arguments"""
    # Create argument parser
    parser = argparse.ArgumentParser(description='Web Research Tool')
    parser.add_argument('--topic', '-t', type=str, required=True, help='Research topic')
    parser.add_argument('--urls', '-u', type=str, nargs='+', required=True, 
                        help='URLs to research (space-separated)')
    parser.add_argument('--loops', '-l', type=int, default=1, help='Number of loops to run')


    # Parse arguments
    args = parser.parse_args()
    
    topic = args.topic
    urls = args.urls
    loops = args.loops
    
    if not urls:
        print("No URLs provided. Exiting.")
        return
    
    for loop in range(loops):
        print(f"Starting Research loop {loop + 1} of {loops}")
        # Perform the research
        research_file = research_topic(urls, topic)
        print(f"Research completed and saved to {research_file}")
        print("Note: If a research file already existed, it was expanded with the new information.")

        if loop > 1:
            time.sleep(10)

    print("Research completed.")

if __name__ == "__main__":
    main()
