"""
This file contains all the prompts used in the YouTube Video Generator project.
Each prompt is defined as a string template that can be formatted with specific variables.
"""

# Research.py Prompts
RESEARCH_EXTRACT_INFO_PROMPT = '''
Based on the following content from {domain}, extract information relevant to the topic: "{topic}".

Requirements:
- Format as a report with title, introduction, body, and conclusion
- Include key dates, figures, statistics, and events
- Define key topics and subtopics
- Analyze and extract important information
- Extract lessons learned
- Extract strategies and tactics
- Ensure historical accuracy
- Be detailed and verbose
- Minimum 1000 words
- University essay style

Content:
{content}

Past Research:
{existingResearch}
'''

RESEARCH_SUMMARY_PROMPT = '''
Create a concise summary of the following research on "{topic}".

Requirements:
- Be clear and concise
- Focus on key points
- Maintain accuracy

Research Content:
{combined_research}
'''

RESEARCH_EXPANSION_PROMPT = '''
Please analyze the following existing research and new information about {topic}.
Combine them into a comprehensive, well-organized research document.

Requirements:
- Remove redundant information
- Ensure content flows logically
- Maintain the same format but improve organization
- Create a cohesive narrative
- Preserve all unique information
- Enhance clarity and readability

Existing Research:
{existing_research}

New Information:
{new_research}

Please provide the expanded research document, maintaining the same format but with improved organization
and no redundant information.
'''

# WorldWar2VideoTranscriptGenerator.py Prompts
TRANSCRIPT_GENERATION_PROMPT = '''
Create a detailed historical transcript for a YouTube video about {topic} during World War II.

Requirements:
- Style: War report format
- Structure:
  * Engaging historical context introduction
  * Chronological coverage of key events
  * Military strategies and tactical decisions
  * Personal stories from soldiers
  * Impact and significance analysis
- Format: Single cohesive block of text
- Tone: Engaging and educational
- Content:
  * Specific dates and locations
  * Key figures
  * Accurate historical details
- Minimum: 1000 words (more is better)
- No section headers or formatting
- Optimized for text-to-speech narration
'''

TRANSCRIPT_WITH_RESEARCH_PROMPT = '''
Create a detailed historical transcript for a YouTube video about {topic} during World War II.

Requirements:
- Style: War report format
- Structure:
  * Engaging historical context introduction
  * Chronological coverage of key events
  * Military strategies and tactical decisions
  * Personal stories from soldiers
  * Impact and significance analysis
- Format: Single cohesive block of text
- Tone: Engaging and educational
- Content:
  * Specific dates and locations
  * Key figures
  * Accurate historical details
- Minimum: 1000 words (more is better)
- No section headers or formatting
- Optimized for text-to-speech narration

Research Content:
{research_content}

Additional Requirements:
- Incorporate key dates, figures, statistics, and events
- Include strategies and personal accounts
- Enhance historical accuracy
'''

# ExpandTranscript.py Prompts
EXPAND_TRANSCRIPT_PROMPT = '''
Rewrite and expand the following historical transcript to create a more detailed and engaging narrative.

Requirements:
- Add approximately {words_needed} more words
- Enhancements:
  * Enrich existing paragraphs with specific details
  * Add relevant historical context
  * Include personal stories and perspectives
  * Ensure smooth transitions
- Format: Single coherent document
- Focus:
  * Historical accuracy
  * Emotional depth
  * Vivid imagery
- No formatting or section headers
- Return as blocks of text for reading aloud
- Quality over quantity - focus on detail and engagement

Transcript:
{current_transcript}
'''

EXPAND_TRANSCRIPT_WITH_RESEARCH_PROMPT = '''
Expand the following transcript to create a more detailed and engaging narrative.
IMPORTANT: You MUST keep ALL existing content and add new content. Do not remove or summarize any existing text.

Requirements:
- Keep ALL existing content exactly as is
- Add {words_needed} new words MINIMUM
- Enhancements:
  * Enrich existing paragraphs with specific details
  * Highlight battles and conflicts
  * Add relevant historical context
  * Include personal stories and perspectives
  * Add new paragraphs with additional information
  * Ensure smooth transitions between new and existing content
- Format: Single coherent document
- Focus:
  * Historical accuracy
  * Emotional depth
  * Vivid imagery
- No formatting or section headers
- Return as blocks of text for reading aloud
- Quality over quantity - focus on detail and engagement

Current Transcript (DO NOT REMOVE ANY OF THIS):
{current_transcript}

Research Content (Use this to add new information):
{research_content}
'''

# GenerateScenes.py Prompts
CLIP_MATCHING_PROMPT = '''
Match video clips to an audio transcript for {transcript_content}.

Available Clips (ID, keywords, length in seconds):
Look in here for clips: {clips_list}

Clip Requirements:
- only use clips that are relevant to the transcript
- only use clips that best represent the context of the transcript
- only use clips matching places, geographics, structures, events, people
- use clips with action in them only 
- do not use clips with text in them
- do not use clips with Sign,Handwriting,Paper,Black,Darkness,Empty,Blank,Unlit,Void,Shadow,Night,Absence,Nothingness
- Match clips to transcript content
- do not use abstract clips
- do not use abstract themes and concepts
- use clips that are more specific and detailed
- Total duration close to {transcript_length} seconds
- Return as JSON array of clip IDs
- Prefer shorter clips

ONLY RETURN THE JSON ARRAY OF CLIP IDs
return Format Json:
["clip-id-1", "clip-id-2", "clip-id-3"]
'''

# Research Matching Prompt
RESEARCH_MATCHING_PROMPT = '''
Analyze the following transcript {transcript} and research materials {research_materials} to find the most relevant research content.

Requirements:
- Return only the most relevant research content
- Focus on content that provides additional context, details, or insights
- Focus on the topic of the transcript
- Focus on characters, places, events, dates, details, tactics, strategies, conflicts, battles, facts, figures, statistics,etc.
- Exclude irrelevant or redundant information
- Format as a single block of text
- Maximum 1000 words total
- Digest the research content and highlight the most relevant parts
'''

# Expansion Idea Prompt
EXPANSION_IDEA_PROMPT = '''
Based on the following transcript {transcript}, identify a new body paragraph to add or the most interesting aspect or what you feel should be expanded with more details.
- Make sure it is not already expanded in the transcript
- DO NOT suggest any of these previously expanded ideas: {previous_ideas}
- Empasize strategic and tactical aspects
- Empasize conflicts and battles
- Do not be too sad or dark
- strategic and tactical aspects
- historical context
- detailed descriptions
- specific names, dates, and events
- try your best to not reduce the word count
Return only the specific aspect/idea to expand, no additional text or formatting.

'''

# TranscriptPurifier.py Prompts
TRANSCRIPT_PURIFIER_PROMPT = '''Maintain exact word count if possible.
Preserve all technical terms, names, and specific details exactly as they appear.
Only make minimal changes needed for clarity, keeping the exact same meaning and all content intact.
Return the complete transcript with minimal edits, maintaining all original information.

Requirements:
- Style: War report format
- Structure:
  * Engaging historical context introduction
  * Chronological coverage of key events
  * Military strategies and tactical decisions
  * Personal stories from soldiers
  * Impact and significance analysis
- Format: Single cohesive block of text
- Tone: Engaging and educational
- Content:
  * Specific dates and locations
  * Key figures
  * Accurate historical details
- No section headers or formatting
- Optimized for text-to-speech narration

We need an introduction to the topic.
We need clear chapters of the text logically seperated and leading to each other.
We need a conclusion to the topic.

NO OTHER FORMATING
NEEDS TO BE IN A BLOCK OF TEXT SEPERATED BY PARAGRAPHS.

{content}
''' 

SCENE_GENERATION_PROMPT = """
I need to match video clips to an audio transcript for a documentary scene. 
The transcript is about: "{transcript_content[:500]}..."

Keywords from transcript: {transcript_keywords}

I need to select clips that visually match this content with a total duration close to {transcript_length} seconds.
Available clips (ID, keywords, length in seconds):
{clips_list[:30]}  # Limiting to first 30 clips to avoid token limits

Select the best matching clips that total approximately {transcript_length} seconds.
Return a JSON array with just the clip IDs in your preferred order, like:
["clip-id-1", "clip-id-2", "clip-id-3"]
"""
SET_CLIP_CSV_KEYWORDS_PROMPT = """
    Based on the following image, select 5-10 relevant keywords or key phrases from the list of available keywords that best represent what is in the image.
    
    Available keywords to choose from:
    {', '.join(available_keywords)}
    
    """
