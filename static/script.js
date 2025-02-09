// Global variables
let currentPdfFilename = null;
let pdfUploaded = false;
let isAutoScrollEnabled = true;
let mediaRecorder;
let audioChunks = [];
let speech = null;
let autoTtsEnabled = false;
let currentAudio = null;
let isSpeechManuallyPaused = false;
let audioQueue = [];
let isProcessingQueue = false;
let lastClickTime = 0;

document.addEventListener('DOMContentLoaded', (event) => {
  processInitialContent();
  attachEventListeners();
  adjustChatAreaHeight();
  attachAudioEventListeners();
  updateButtonVisibility();
});

function attachEventListeners() {
  const sendButton = document.getElementById("send-button");
  const userInput = document.getElementById("user_input");
  const settingsButton = document.getElementById('settings-button');
  const modelSelect = document.getElementById('model_select');
  const attachButton = document.getElementById('attach-button');
  const fileUpload = document.getElementById('file-upload');
  const removePdfButton = document.getElementById('remove-pdf');
  const chatArea = document.getElementById("chat_area");
  const ttsLanguageSelect = document.getElementById('tts_language');
  const autoTtsCheckbox = document.getElementById('auto_tts');
  const disableSearchSwitch = document.getElementById('disable_search');
  const disableSearchHidden = document.getElementById('disable_search_hidden');

  if (disableSearchSwitch && disableSearchHidden) {
    disableSearchSwitch.addEventListener('change', function() {
      console.log('Web search:', this.checked);
      disableSearchHidden.value = !this.checked;
    });
  }

  if (ttsLanguageSelect) {
    ttsLanguageSelect.addEventListener('change', function() {
      const selectedLang = this.value;
      console.log('TTS language changed to:', selectedLang);
    });
  }

  if (autoTtsCheckbox) {
    autoTtsCheckbox.addEventListener('change', function() {
      autoTtsEnabled = this.checked;
      console.log('Auto TTS Enabled:', this.checked);
    });
  }

  if (sendButton) {
    sendButton.addEventListener("click", sendMessage);
  }

  if (userInput) {
    userInput.addEventListener('input', function() {
      adjustTextareaHeight.call(this);
      updateButtonVisibility();
    });

    userInput.addEventListener('keypress', handleEnterPress);
  }

  if (settingsButton) {
    settingsButton.addEventListener('click', toggleSettings);
  }

  if (modelSelect) {
    modelSelect.addEventListener('change', handleModelChange);
  }

  if (attachButton) {
    attachButton.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
    
      const currentTime = new Date().getTime();
      if (currentTime - lastClickTime < 1000) { // Prevent double trigger within 1 second
        return;
      }
      lastClickTime = currentTime;

      if (!isUploading) {
        const input = document.getElementById('file-upload');
        input.value = ''; // Reset input value
        input.click();
      }
    });
  }

  if (fileUpload) {
    fileUpload.addEventListener('change', (event) => {
      event.stopPropagation();
      handleFileUpload(event);
    });
  }

  if (removePdfButton) {
    removePdfButton.addEventListener('click', removePdf);
  }

  if (chatArea) {
    chatArea.addEventListener("scroll", handleManualScroll);
    chatArea.addEventListener("touchstart", function() {
      isAutoScrollEnabled = false;
    });

    chatArea.addEventListener("touchend", function() {
      const isScrolledToBottom = chatArea.scrollHeight - chatArea.clientHeight <= chatArea.scrollTop + 1;
      isAutoScrollEnabled = isScrolledToBottom;
    });
  }

  window.addEventListener('resize', adjustChatAreaHeight);

  applyHighlightingAndCopyButtons();
  attachAudioEventListeners();
}

function processInitialContent() {
  document.querySelectorAll('.assistant-message.initial-content').forEach((messageDiv) => {
    const content = messageDiv.textContent;
    messageDiv.innerHTML = marked.parse(content);
    applyHighlightingAndCopyButtons();
  });
}

let isUploading = false;

function handleFileUpload(event) {
  if (isUploading) return;

  const file = event.target.files[0];
  if (!file) return;

  isUploading = true;
  const formData = new FormData();
  formData.append('file', file);

  const loadingIndicator = document.getElementById('loading-indicator');
  loadingIndicator.style.display = 'block';

  fetch('/', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    showFlashMessage(data.message);
    currentPdfFilename = file.name;
    pdfUploaded = true;
    displayPdfInfo(file.name);
    adjustChatAreaHeight();
    scrollToBottom();

    // Disable web search option
    const disableSearchSwitch = document.getElementById('disable_search');
    if (disableSearchSwitch) {
      disableSearchSwitch.checked = false;
      disableSearchSwitch.dispatchEvent(new Event('change'));
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showFlashMessage('An error occurred while uploading the file.');
  })
  .finally(() => {
    loadingIndicator.style.display = 'none';
    isUploading = false;
    // Reset the file input
    event.target.value = '';
  });
}

function showFlashMessage(message) {
  const flashContainer = document.getElementById('flash-message-container');
  const flashMessage = document.createElement('div');
  flashMessage.className = 'flash-message';
  flashMessage.textContent = message;
  flashContainer.appendChild(flashMessage);

  setTimeout(() => {
    flashContainer.removeChild(flashMessage);
  }, 5000);
}

function displayPdfInfo(filename) {
  const pdfInfo = document.getElementById('pdf-info');
  const pdfFilename = document.getElementById('pdf-filename');
  const userInput = document.getElementById("user_input");
  pdfFilename.textContent = filename;
  pdfInfo.style.display = 'block';

  // Move the PDF info above the user input
  const inputContainer = document.querySelector('.input-container');
  inputContainer.insertBefore(pdfInfo, inputContainer.firstChild);

  adjustTextareaHeight.call(userInput);

  // Re-enable web search option
  const disableSearchSwitch = document.getElementById('disable_search');
  if (disableSearchSwitch) {
    disableSearchSwitch.checked = true;
    disableSearchSwitch.dispatchEvent(new Event('change'));
  }
}

function removePdf() {
  const fileUpload = document.getElementById('file-upload');
  const pdfInfo = document.getElementById('pdf-info');
  fileUpload.value = '';
  pdfInfo.style.display = 'none';
  currentPdfFilename = null;
  pdfUploaded = false;

  adjustTextareaHeight.call(document.getElementById("user_input"));
}

function sendMessage(event) {
  event.preventDefault();
  stopAllSpeech();
  const userInput = document.getElementById("user_input");
  const userInputValue = userInput.value.trim();
  const disableSearchSwitch = document.getElementById('disable_search');

  if (userInputValue === '' && !pdfUploaded) {
    showFlashMessage('Please enter a message or upload a PDF');
    return;
  }

  const formData = new FormData(document.getElementById("query-form"));
  let messageContent = userInputValue;
  if (pdfUploaded && currentPdfFilename) {
    messageContent = `[${currentPdfFilename}]\n${messageContent}`;
    pdfUploaded = false; // Reset the flag after sending the message
  }
  // Ensure the value of disable_search is sent correctly
  const isSearchDisabled = !disableSearchSwitch.checked;
  formData.append('user_input', messageContent);
  formData.append('model_select', document.getElementById('model_select').value);
  formData.append('disable_search', isSearchDisabled.toString());

  const conversationHistory = JSON.parse(document.getElementById('conversation_history').value);
  conversationHistory.push({ role: 'user', content: messageContent });
  document.getElementById('conversation_history').value = JSON.stringify(conversationHistory);

  appendMessage(messageContent, false);
  userInput.value = '';
  updateButtonVisibility();

  // Hide PDF info after sending the message, but keep the filename
  document.getElementById('pdf-info').style.display = 'none';

  createAssistantMessage();
  adjustChatAreaHeight();
  scrollToBottom();

  fetch('/stream', {
    method: 'POST',
    body: formData
  }).then(response => {
    const reader = response.body.getReader();
    return streamResponse(reader);
  }).then(() => {
    const lastAssistantMessage = document.querySelector('.assistant-message:last-child');
    if (lastAssistantMessage) {
      const contentDiv = lastAssistantMessage.querySelector('.message-content') || lastAssistantMessage;
      const renderedText = contentDiv.innerText;
      if (autoTtsEnabled) {
        speakText(renderedText, true);
      }
    }
  }).catch(error => {
    console.error('Error:', error);
    finishAssistantMessage('Error: Could not get response from server.');
  });
}

function streamResponse(reader) {
  let contentBuffer = '';
  let isSearchMode = false;
  const decoder = new TextDecoder();

  function processText({ done, value }) {
    if (done) {
      finishAssistantMessage(contentBuffer);
      return;
    }

    const chunk = decoder.decode(value, { stream: true });
    // Check for search mode signal
    if (chunk.includes('SEARCH_MODE')) {
        isSearchMode = true;
        const assistantMessage = document.querySelector('.assistant-message.thinking-animation');
        if (assistantMessage) {
            assistantMessage.classList.remove('thinking-animation');
            assistantMessage.classList.add('searching-animation');
        }
        return reader.read().then(processText);
    }

    contentBuffer += chunk;

    if (!window.updateTimeout) {
      window.updateTimeout = setTimeout(() => {
        updateAssistantMessage(contentBuffer, isSearchMode);
        window.updateTimeout = null;
      }, 11);
    }

    return reader.read().then(processText);
  }

  return reader.read().then(processText);
}

function appendMessage(content, isAssistant) {
  const chatArea = document.getElementById("chat_area");
  const messageDiv = document.createElement('div');
  messageDiv.className = isAssistant ? 'message assistant-message' : 'message user-message';

  const contentDiv = document.createElement('div');
  contentDiv.className = isAssistant ? 'assistant-message-content' : 'message-content';

  if (isAssistant) {
    contentDiv.innerHTML = marked.parse(content);
    applyHighlightingAndCopyButtons();
    messageDiv.appendChild(contentDiv);
    addTtsButton(messageDiv, content);
  } else {
    contentDiv.textContent = content;
    messageDiv.appendChild(contentDiv);
  }

  chatArea.appendChild(messageDiv);
  scrollToBottom();
}

function createAssistantMessage() {
  const chatArea = document.getElementById("chat_area");
  const assistantMessage = document.createElement('div');
  assistantMessage.className = 'message assistant-message thinking-animation';
  chatArea.appendChild(assistantMessage);
  scrollToBottom();
  return assistantMessage;
}

function updateAssistantMessage(content, isSearchMode) {
  const assistantMessage = document.querySelector('.assistant-message.thinking-animation, .assistant-message.searching-animation');
  if (assistantMessage) {
    assistantMessage.classList.remove('thinking-animation', 'searching-animation');
    const contentDiv = assistantMessage.querySelector('.message-content') || assistantMessage;
    contentDiv.innerHTML = marked.parse(content);
    applyHighlightingAndCopyButtons();
    if (!assistantMessage.querySelector('.tts-button')) {
      addTtsButton(assistantMessage, content);
    }
    scrollToBottom();
  } else {
    const lastAssistantMessage = document.querySelector('.assistant-message:last-child');
    if (lastAssistantMessage) {
      const contentDiv = lastAssistantMessage.querySelector('.message-content') || lastAssistantMessage;
      contentDiv.innerHTML = marked.parse(content);
      applyHighlightingAndCopyButtons();
      if (!lastAssistantMessage.querySelector('.tts-button')) {
        addTtsButton(lastAssistantMessage, content);
      }
      scrollToBottom();
    }
  }
}

function finishAssistantMessage(content) {
  const assistantMessage = document.querySelector('.assistant-message.thinking-animation');
  if (assistantMessage) {
    assistantMessage.classList.remove('thinking-animation');
    const contentDiv = assistantMessage.querySelector('.message-content') || assistantMessage;
    contentDiv.innerHTML = marked.parse(content);
    applyHighlightingAndCopyButtons();
    if (!assistantMessage.querySelector('.tts-button')) {
      addTtsButton(assistantMessage, content);
    }
    scrollToBottom();

    const conversationHistory = JSON.parse(document.getElementById('conversation_history').value);
    conversationHistory.push({ role: 'assistant', content: content });
    document.getElementById('conversation_history').value = JSON.stringify(conversationHistory);
    const renderedText = contentDiv.innerText;
    if (autoTtsEnabled && !isSpeechManuallyPaused && !currentSpeech) {
      speakText(renderedText, assistantMessage.querySelector('.tts-button'));
    }
  }
  updateButtonVisibility();
}

function handleManualScroll() {
  const chatArea = document.getElementById("chat_area");
  const isScrolledToBottom = chatArea.scrollHeight - chatArea.clientHeight <= chatArea.scrollTop + 1;
  isAutoScrollEnabled = isScrolledToBottom;
}

function scrollToBottom() {
  const chatArea = document.getElementById("chat_area");
  if (isAutoScrollEnabled) {
    chatArea.scrollTop = chatArea.scrollHeight;
  }
}

function adjustChatAreaHeight() {
  const inputWrapper = document.querySelector('.input-wrapper');
  const inputHeight = inputWrapper.offsetHeight;
  const chatArea = document.getElementById('chat_area');
  chatArea.style.maxHeight = `calc(100vh - ${inputHeight + 100}px)`;
}

function adjustTextareaHeight() {
  this.style.height = 'auto';
  this.style.height = (this.scrollHeight) + 'px';
  adjustChatAreaHeight();
}

function handleEnterPress(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage(e);
  }
}

function toggleSettings() {
  const assistantPromptWrapper = document.getElementById('assistant-prompt-wrapper');
  if (assistantPromptWrapper.style.display === 'none' || assistantPromptWrapper.style.display === '') {
    assistantPromptWrapper.style.display = 'block';
    assistantPromptWrapper.style.opacity = '0';
    assistantPromptWrapper.style.visibility = 'hidden';
    setTimeout(() => {
      assistantPromptWrapper.style.opacity = '1';
      assistantPromptWrapper.style.visibility = 'visible';
    }, 10);
  } else {
    assistantPromptWrapper.style.opacity = '0';
    assistantPromptWrapper.style.visibility = 'hidden';
    setTimeout(() => {
      assistantPromptWrapper.style.display = 'none';
    }, 300);
  }
}

function handleModelChange() {
  console.log('Model changed to:', this.value);
}

function applyHighlightingAndCopyButtons() {
  document.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);

    const pre = block.closest('pre');
    if (!pre.querySelector('.copy-button')) {
      const button = document.createElement('button');
      button.className = 'copy-button';
      button.textContent = 'Copy';
      button.addEventListener('click', (e) => {
        e.preventDefault();
        const code = pre.querySelector('code');
        navigator.clipboard.writeText(code.textContent).then(() => {
          button.textContent = 'Copied!';
          setTimeout(() => {
            button.textContent = 'Copy';
          }, 2000);
        }).catch(err => {
          console.error('Failed to copy text: ', err);
        });
      });
      pre.appendChild(button);
    }
  });
}

function startRecording() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.start();

      mediaRecorder.addEventListener("dataavailable", event => {
        audioChunks.push(event.data);
      });

      hideElement('start-recording');
      showElement('stop-recording');
    })
    .catch(error => {
      console.error('Error accessing microphone:', error);
      showFlashMessage('Error accessing microphone: ' + error.message);
    });
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();

    mediaRecorder.addEventListener("stop", () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      audioChunks = [];

      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.wav");

      fetch('/transcribe', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.transcript) {
          document.getElementById('user_input').value = data.transcript;
          sendMessage(new Event('submit'));
        } else {
          console.error('Transcription failed:', data.error);
          showFlashMessage('Transcription failed: ' + data.error);
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showFlashMessage('Error during transcription: ' + error.message);
      });

      hideElement('stop-recording');
      showElement('start-recording');
    });
  }
}

function attachAudioEventListeners() {
  const startRecordingButton = document.getElementById('start-recording');
  const stopRecordingButton = document.getElementById('stop-recording');

  if (startRecordingButton) {
    startRecordingButton.addEventListener('click', startRecording);
  }

  if (stopRecordingButton) {
    stopRecordingButton.addEventListener('click', stopRecording);
  }
}

function showElement(elementId) {
  document.getElementById(elementId).style.display = 'inline-block';
}

function hideElement(elementId) {
  document.getElementById(elementId).style.display = 'none';
}

function updateButtonVisibility() {
  const userInput = document.getElementById('user_input');
  const sendButton = document.getElementById('send-button');
  const startRecordingButton = document.getElementById('start-recording');
  const stopRecordingButton = document.getElementById('stop-recording');

  if (userInput.value.trim() !== '') {
    showElement('send-button');
    hideElement('start-recording');
    hideElement('stop-recording');
  } else {
    hideElement('send-button');
    showElement('start-recording');
    hideElement('stop-recording');
  }
}

function handleRecordingError(error) {
  console.error('Error starting recording:', error);
  showFlashMessage('Error starting recording: ' + error.message);
  showElement('start-recording');
  hideElement('stop-recording');
}

async function speakText(text, button = null) {
    console.log("speakText function called");
    try {
        if (button && button.dataset) {
            button.textContent = '🔄'; // Loading indicator
            button.dataset.speaking = 'loading';
        }

        const cleanText = text.replace(/🔊|🔇|🔄/g, '').trim();
        const selectedLang = getSelectedTtsLanguage();
        
        // Stop current audio if playing
        if (currentAudio) {
            stopSpeaking(false);
        }

        const response = await fetch('/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: cleanText,
                language: selectedLang
            })
        });
        
        if (!response.ok) {
            throw new Error(`TTS request failed: ${response.status} ${response.statusText}`);
        }
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        currentAudio = audio;
        
        audio.oncanplaythrough = function() {
            if (button && button.dataset) {
                button.textContent = '🔇';
                button.dataset.speaking = 'true';
            }
        };
        
        audio.onended = function() {
            if (button && button.dataset) {
                button.textContent = '🔊';
                button.dataset.speaking = 'false';
            }
            URL.revokeObjectURL(audioUrl);
            currentAudio = null;
            
            if (autoTtsEnabled && !isSpeechManuallyPaused) {
                const nextMessage = findNextUnspokenMessage();
                if (nextMessage) {
                    const cleanText = getMessageTextForTTS(nextMessage);
                    const nextButton = nextMessage.querySelector('.tts-button');
                    speakText(cleanText, nextButton);
                } else {
                    isSpeechManuallyPaused = false;
                }
            }
        };
        
        audio.onerror = function(e) {
            console.error("Audio playback error:", e);
            if (button && button.dataset) {
                button.textContent = '🔊';
                button.dataset.speaking = 'false';
            }
            URL.revokeObjectURL(audioUrl);
            currentAudio = null;
            showFlashMessage('Error playing audio');
        };

        try {
            await audio.play();
        } catch (playError) {
            console.error('Error playing audio:', playError);
            if (button && button.dataset) {
                button.textContent = '🔊';
                button.dataset.speaking = 'false';
            }
            URL.revokeObjectURL(audioUrl);
            currentAudio = null;
            throw playError;
        }
        
    } catch (error) {
        console.error('Error in TTS:', error);
        if (button && button.dataset) {
            button.textContent = '🔊';
            button.dataset.speaking = 'false';
        }
        showFlashMessage('Error in text-to-speech: ' + error.message);
    }
}

function getMessageTextForTTS(messageElement) {
    const contentElement = messageElement.querySelector('.message-content') || messageElement;
    let text = contentElement.innerText;
    // Bersihkan teks dari emoji TTS button dan whitespace berlebih
    return text.replace(/🔊|🔇|🔄/g, '').trim();
}

function findNextUnspokenMessage() {
    const messages = document.querySelectorAll('.assistant-message');
    let foundCurrent = false;
    
    for (let message of messages) {
        const ttsButton = message.querySelector('.tts-button');
        
        // Jika kita menemukan pesan yang sedang diputar
        if (!foundCurrent && ttsButton && ttsButton.dataset.speaking === 'true') {
            foundCurrent = true;
            continue;
        }
        
        // Setelah menemukan pesan yang sedang diputar, cari pesan berikutnya
        if (foundCurrent && ttsButton && ttsButton.dataset.speaking === 'false') {
            return message;
        }
    }
    return null;
}

function stopSpeaking(manualStop = false) {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
    
    if (manualStop) {
        isSpeechManuallyPaused = true;
    }
    
    const ttsButtons = document.querySelectorAll('.tts-button');
    ttsButtons.forEach(btn => {
        btn.textContent = '🔊';
        btn.dataset.speaking = 'false';
    });
}

function toggleSpeech(button, text) {
    if (button && button.dataset && button.dataset.speaking === 'true') {
        stopSpeaking(true);
    } else {
        isSpeechManuallyPaused = false;
        const cleanText = getMessageTextForTTS(button.closest('.message'));
        speakText(cleanText, button);
    }
}


function addTtsButton(messageElement, messageText) {
    if (messageElement.querySelector('.tts-button')) return;

    const ttsButton = document.createElement('button');
    ttsButton.className = 'tts-button';
    ttsButton.textContent = '🔊';
    ttsButton.dataset.speaking = 'false';
    
    ttsButton.addEventListener('click', (e) => {
        e.preventDefault();
        const contentElement = messageElement.querySelector('.message-content') || messageElement;
        const renderedText = contentElement.innerText;
        toggleSpeech(ttsButton, renderedText);
    });

    messageElement.appendChild(ttsButton);
}

window.addEventListener('beforeunload', stopAllSpeech);

function stopAllSpeech() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
    audioQueue = [];
    isProcessingQueue = false;
    const ttsButtons = document.querySelectorAll('.tts-button');
    ttsButtons.forEach(btn => btn.textContent = '🔊');
}

function getSelectedTtsLanguage() {
  const ttsLanguageSelect = document.getElementById('tts_language');
  return ttsLanguageSelect ? ttsLanguageSelect.value : 'en-US'; // Default to English if not found
}

const style = document.createElement('style');
style.textContent = `
    .tts-button[data-speaking='loading'] {
        opacity: 0.7;
        cursor: wait;
    }
    .tts-button[data-speaking='true'] {
        background-color: #ff4444;
    }
    .tts-button[data-speaking='false'] {
        background-color: #4CAF50;
    }
`;
document.head.appendChild(style);

// Initialize
attachEventListeners();
adjustChatAreaHeight();