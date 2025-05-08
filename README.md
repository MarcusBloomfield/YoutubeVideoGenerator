# YouTube Video Generator 

This App automatically generates faceless YouTube videos and uploads them using OpenAi for script generation, Eleven labs for voice over and Google api for YouTube uploading.

Examples: https://www.youtube.com/@AiHistory-e2o/shorts

## Workflow

1. Clips are input into the app and then it saves them to a database with a description of what is happening in the clips using OpenAi vision.

2. It then asks the user what kind of script it would like to make using the clips.

3. It then utilizses OpenAi to build the video assigning relevant clips to what is happening in the script.

4. Finally it uploads the video to YouTube, generates a name, description and hastags for the video then publishes it.
