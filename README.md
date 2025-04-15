# YouTube Video Uploader

This script automatically uploads videos from the `Output` folder to YouTube, generating appropriate titles, descriptions, thumbnails, and tags using AI.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up YouTube API credentials:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the YouTube Data API v3
   - Go to Credentials
   - Create OAuth 2.0 Client ID credentials
   - Download the client secrets file and save it as `client_secrets.json` in the project directory

3. Set up OpenAI API:
   - Get your API key from [OpenAI](https://platform.openai.com/api-keys)
   - Create a `.env` file in the project directory with:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Place your MP4 videos in the `Output` folder.

2. Run the uploader:
```bash
python YoutubeUploader.py
```

The script will:
- Generate engaging titles, descriptions, and tags using AI
- Create thumbnails from the videos
- Upload videos to YouTube (initially as private)
- Move processed videos to `Output/uploaded` with timestamps

## Features

- OAuth 2.0 authentication with credential persistence
- AI-generated metadata using GPT-4
- Automatic thumbnail generation
- Progress tracking for uploads
- Organized file management
- Error handling and logging

## Notes

- Videos are uploaded as private by default for review
- Thumbnails are generated from frames 20% into the video
- Failed uploads are left in the Output folder for retry
- Successful uploads are moved to Output/uploaded with timestamps 