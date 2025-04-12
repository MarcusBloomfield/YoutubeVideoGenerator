// Wait for the DOM to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to the clicked button and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            // Call specific init functions for tabs that need to load data
            if (tabId === 'transcript-expand') {
                loadTranscriptFiles();
            } else if (tabId === 'raw-video') {
                loadRawVideoFiles();
            } else if (tabId === 'log') {
                // Load system information when log tab is opened
                loadSystemInfo();
            }
        });
    });

    // Load API key from storage if available
    const apiKey = localStorage.getItem('openai_api_key');
    if (apiKey) {
        document.getElementById('api-key').value = apiKey;
    }

    // Save settings
    document.getElementById('save-settings').addEventListener('click', async function() {
        const apiKey = document.getElementById('api-key').value;
        localStorage.setItem('openai_api_key', apiKey);
        
        // Send API key to Python
        await eel.set_api_key(apiKey)();
        showMessage('Settings saved successfully!', 'success');
    });

    // Transcript generation
    document.getElementById('generate-transcript').addEventListener('click', async function() {
        const topic = document.getElementById('topic').value;
        
        if (!topic) {
            showMessage('Please enter a topic', 'error');
            return;
        }

        showProgress('Generating transcript...');
        
        try {
            // Generate the transcript
            const result = await eel.generate_transcript(topic)();
            
            // Get the actual transcript file content
            const transcriptContent = await eel.get_latest_transcript_content()();
            
            // Display the file content in the textarea
            document.getElementById('transcript-output').value = transcriptContent;
            
            hideProgress();
            showMessage('Transcript generated successfully!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error generating transcript: ' + error, 'error');
        }
    });

    // Clips processing buttons
    document.getElementById('purify-clips').addEventListener('click', async function() {
        showProgress('Purifying clips data...');
        try {
            const result = await eel.purify_clips_data()();
            document.getElementById('clips-output').value = result;
            hideProgress();
            showMessage('Clips data purified!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error purifying clips: ' + error, 'error');
        }
    });

    document.getElementById('extract-clips').addEventListener('click', async function() {
        showProgress('Extracting clips...');
        try {
            const result = await eel.extract_clips()();
            document.getElementById('clips-output').value = result;
            hideProgress();
            showMessage('Clips extracted!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error extracting clips: ' + error, 'error');
        }
    });

    document.getElementById('set-keywords').addEventListener('click', async function() {
        showProgress('Setting clip keywords...');
        try {
            const result = await eel.set_clip_keywords()();
            document.getElementById('clips-output').value = result;
            hideProgress();
            showMessage('Keywords set!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error setting keywords: ' + error, 'error');
        }
    });

    document.getElementById('parse-to-csv').addEventListener('click', async function() {
        showProgress('Parsing clips to CSV...');
        try {
            const result = await eel.parse_to_csv()();
            document.getElementById('clips-output').value = result;
            hideProgress();
            showMessage('Clips parsed to CSV!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error parsing to CSV: ' + error, 'error');
        }
    });

    // Scenes generation
    document.getElementById('generate-scenes').addEventListener('click', async function() {
        showProgress('Generating scenes...');
        try {
            const result = await eel.generate_scenes()();
            document.getElementById('scenes-output').value = result;
            hideProgress();
            showMessage('Scenes generated!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error generating scenes: ' + error, 'error');
        }
    });

    // Narration creation
    document.getElementById('create-narration').addEventListener('click', async function() {
        showProgress('Creating narration...');
        try {
            const result = await eel.create_narration()();
            document.getElementById('narration-output').value = result;
            hideProgress();
            showMessage('Narration created!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error creating narration: ' + error, 'error');
        }
    });

    // Combine media
    document.getElementById('combine-media').addEventListener('click', async function() {
        showProgress('Combining video and audio...');
        try {
            const outputName = document.getElementById('output-name').value;
            const result = await eel.combine_media(outputName)();
            document.getElementById('combine-output').value = result;
            hideProgress();
            showMessage('Media combined!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error combining media: ' + error, 'error');
        }
    });
    
    // NEW: Transcript Expansion functions
    document.getElementById('refresh-transcripts').addEventListener('click', function() {
        loadTranscriptFiles();
    });
    
    document.getElementById('expand-transcript').addEventListener('click', async function() {
        const transcriptSelect = document.getElementById('transcript-select');
        const selectedTranscript = transcriptSelect.value;
        
        if (!selectedTranscript) {
            showMessage('Please select a transcript file', 'error');
            return;
        }
        
        const loops = document.getElementById('expansion-loops').value;
        const targetWords = document.getElementById('target-words').value;
        
        showProgress('Expanding transcript...');
        
        try {
            const result = await eel.expand_transcript_file(selectedTranscript, loops, targetWords)();
            document.getElementById('expansion-output').value = result;
            hideProgress();
            showMessage('Transcript expanded successfully!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error expanding transcript: ' + error, 'error');
        }
    });
    
    // Function to load transcript files
    async function loadTranscriptFiles() {
        try {
            const transcriptFiles = await eel.get_transcript_files()();
            const select = document.getElementById('transcript-select');
            
            // Clear existing options
            select.innerHTML = '';
            
            if (transcriptFiles.length === 0) {
                const option = document.createElement('option');
                option.text = 'No transcript files found';
                option.disabled = true;
                select.add(option);
            } else {
                transcriptFiles.forEach(file => {
                    const option = document.createElement('option');
                    option.value = file;
                    option.text = file;
                    select.add(option);
                });
            }
        } catch (error) {
            showMessage('Error loading transcript files: ' + error, 'error');
        }
    }
    
    // NEW: Research functions
    document.getElementById('research-topic-btn').addEventListener('click', async function() {
        const topic = document.getElementById('research-topic').value;
        const urls = document.getElementById('research-urls').value;
        const loops = document.getElementById('research-loops').value;
        
        if (!topic) {
            showMessage('Please enter a research topic', 'error');
            return;
        }
        
        if (!urls) {
            showMessage('Please enter at least one URL', 'error');
            return;
        }
        
        showProgress('Researching topic...');
        
        try {
            const result = await eel.research_topic(topic, urls, loops)();
            document.getElementById('research-output').value = result;
            hideProgress();
            showMessage('Research completed successfully!', 'success');
        } catch (error) {
            hideProgress();
            showMessage('Error during research: ' + error, 'error');
        }
    });
    
    // NEW: Raw Video Management functions
    document.getElementById('refresh-videos').addEventListener('click', function() {
        loadRawVideoFiles();
    });
    
    document.getElementById('rename-videos').addEventListener('click', async function() {
        const appendString = document.getElementById('append-string').value;
        
        showProgress('Renaming raw video files...');
        
        try {
            const result = await eel.rename_raw_videos(appendString)();
            document.getElementById('raw-video-output').value = result;
            hideProgress();
            showMessage('Videos renamed successfully!', 'success');
            loadRawVideoFiles(); // Refresh the list
        } catch (error) {
            hideProgress();
            showMessage('Error renaming videos: ' + error, 'error');
        }
    });
    
    // Function to load raw video files
    async function loadRawVideoFiles() {
        try {
            const videoFiles = await eel.get_raw_video_files()();
            const select = document.getElementById('video-files');
            
            // Clear existing options
            select.innerHTML = '';
            
            if (videoFiles.length === 0) {
                const option = document.createElement('option');
                option.text = 'No video files found';
                option.disabled = true;
                select.add(option);
            } else {
                videoFiles.forEach(file => {
                    const option = document.createElement('option');
                    option.value = file;
                    option.text = file;
                    select.add(option);
                });
            }
        } catch (error) {
            showMessage('Error loading video files: ' + error, 'error');
        }
    }

    // Function to load system information
    async function loadSystemInfo() {
        try {
            const systemInfo = await eel.get_system_info()();
            
            if (systemInfo.error) {
                add_log(`Error getting system info: ${systemInfo.error}`, 'error');
                return;
            }
            
            add_log('---------- SYSTEM INFORMATION ----------', 'info');
            add_log(`Operating System: ${systemInfo.os}`, 'info');
            add_log(`Python Version: ${systemInfo.python_version.split(' ')[0]}`, 'info');
            add_log(`Time: ${systemInfo.timestamp}`, 'info');
            
            add_log('---------- DIRECTORIES ----------', 'info');
            for (const [dir, exists] of Object.entries(systemInfo.directories)) {
                const status = exists ? '✓ Exists' : '✗ Missing';
                add_log(`${dir}: ${status}`, exists ? 'info' : 'warning');
            }
            
            add_log('---------- KEY FILES ----------', 'info');
            for (const [file, exists] of Object.entries(systemInfo.key_files)) {
                const status = exists ? '✓ Exists' : '✗ Missing';
                add_log(`${file}: ${status}`, exists ? 'info' : 'warning');
            }
            
            add_log('---------- READY ----------', 'info');
        } catch (error) {
            add_log(`Error loading system information: ${error}`, 'error');
        }
    }

    // Add progress update function for the Python callbacks
    function update_progress(percent, message) {
        const progressBar = document.getElementById('progress-bar-fill');
        const progressText = document.getElementById('progress-text');
        
        if (progressBar && progressText) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
            
            const displayMessage = message || `${percent}% Complete`;
            progressText.textContent = `${percent}% - ${displayMessage}`;
        }
    }

    // Add log window controls
    document.getElementById('clear-log').addEventListener('click', function() {
        document.getElementById('log-content').innerHTML = '';
        add_log('Log cleared', 'info');
    });
    
    document.getElementById('save-log').addEventListener('click', function() {
        const logContent = document.getElementById('log-content').innerText;
        
        // Create a blob and download link
        const blob = new Blob([logContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `video-generator-log-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        add_log('Log saved to file', 'info');
    });
    
    document.getElementById('log-level').addEventListener('change', function() {
        const selectedLevel = this.value;
        const logEntries = document.querySelectorAll('.log-entry');
        
        logEntries.forEach(entry => {
            if (selectedLevel === 'all') {
                entry.style.display = 'block';
            } else {
                if (entry.classList.contains(selectedLevel)) {
                    entry.style.display = 'block';
                } else {
                    entry.style.display = 'none';
                }
            }
        });
        
        add_log(`Log filter set to: ${selectedLevel}`, 'info');
    });
    
    // Add initial log entry
    setTimeout(() => {
        add_log('Log system initialized', 'info');
        add_log('Welcome to YouTube Video Generator', 'info');
    }, 500);
});

// Utility functions
function showProgress(message) {
    const progressContainer = document.getElementById('progress-container');
    const progressText = document.getElementById('progress-text');
    
    progressContainer.classList.remove('hidden');
    progressText.textContent = `0% - ${message || 'Processing...'}`;
    
    // Reset progress bar
    document.getElementById('progress-bar-fill').style.width = '0%';
    
    // Log the start of the process
    add_log(`Started: ${message || 'Processing...'}`, 'info');
    
    // Animate progress bar
    let width = 0;
    const interval = setInterval(() => {
        if (width >= 90) {
            clearInterval(interval);
        } else {
            width += Math.random() * 5;
            document.getElementById('progress-bar-fill').style.width = width + '%';
        }
    }, 500);
}

function hideProgress() {
    const progressContainer = document.getElementById('progress-container');
    progressContainer.style.display = 'none';
}

function showMessage(message, type = 'info') {
    // Show a toast message
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Auto-remove after a delay
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => document.body.removeChild(toast), 500);
    }, 3000);
}

// Expose JavaScript functions to Python
eel.expose(update_progress);
function update_progress(percent, message) {
    const progressBar = document.getElementById('progress-bar-fill');
    const progressText = document.getElementById('progress-text');
    
    if (progressBar && progressText) {
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        
        const displayMessage = message || `${percent}% Complete`;
        progressText.textContent = `${percent}% - ${displayMessage}`;
    }
}

// NEW: Log functionality
eel.expose(add_log);
function add_log(message, level = 'info') {
    const logContent = document.getElementById('log-content');
    if (!logContent) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${level}`;
    
    let levelText = '';
    switch (level) {
        case 'info':
            levelText = 'INFO';
            break;
        case 'warning':
            levelText = 'WARNING';
            break;
        case 'error':
            levelText = 'ERROR';
            break;
        default:
            levelText = 'INFO';
    }
    
    logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> <span class="log-level">[${levelText}]</span> ${message}`;
    logContent.appendChild(logEntry);
    
    // Auto-scroll if enabled
    if (document.getElementById('auto-scroll') && document.getElementById('auto-scroll').checked) {
        logContent.scrollTop = logContent.scrollHeight;
    }
    
    // Apply filter if needed
    const selectedLevel = document.getElementById('log-level').value;
    if (selectedLevel !== 'all' && level !== selectedLevel) {
        logEntry.style.display = 'none';
    }
}