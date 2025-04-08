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
Rewrite and expand the following historical transcript to create a more detailed and engaging narrative.

Requirements:
- Add approximately {words_needed} more words
- Enhancements:
  * Enrich existing paragraphs with specific details
  * Highlight battles and conflicts
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

Research Materials:
{research_content}

Additional Requirements:
- Incorporate relevant facts and details
- Include specific names, dates, and events
- Add descriptive details from research
'''

# GenerateScenes.py Prompts
CLIP_MATCHING_PROMPT = '''
Match video clips to an audio transcript for a documentary scene.

Requirements:
- Match clips to transcript content
- Total duration close to {transcript_length} seconds
- Return as JSON array of clip IDs

Transcript:
{transcript_content}

Available Clips (ID, keywords, length in seconds):
{clips_list}

Format:
["clip-id-1", "clip-id-2", "clip-id-3"]
'''

# Research Matching Prompt
RESEARCH_MATCHING_PROMPT = '''
Analyze the following transcript and research materials to find the most relevant research content.

Transcript:
{transcript}

Research Materials:
{research_materials}

Requirements:
- Return only the most relevant research content
- Focus on content that provides additional context, details, or insights
- Exclude irrelevant or redundant information
- Format as a single block of text
- Maximum 3000 words total
- Maintain original formatting and structure
''' 