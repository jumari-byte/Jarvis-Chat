// Global variables
let currentPdfFilename = null;
let pdfUploaded = false;
let isAutoScrollEnabled = true;

document.addEventListener('DOMContentLoaded', (event) => {
  processInitialContent();
  attachEventListeners();
  adjustChatAreaHeight();
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

  if (sendButton) {
    sendButton.addEventListener("click", sendMessage);
  }

  if (userInput) {
    userInput.addEventListener('input', adjustTextareaHeight);
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
      if (!isUploading) {
        fileUpload.click();
      }
    });
  }

  if (fileUpload) {
    fileUpload.addEventListener('change', handleFileUpload);
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
}

function processInitialContent() {
  document.querySelectorAll('.assistant-message.initial-content').forEach((messageDiv) => {
    const content = messageDiv.textContent;
    messageDiv.innerHTML = marked.parse(content);
  });
  applyHighlightingAndCopyButtons();
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
  const userInput = document.getElementById("user_input");
  const userInputValue = userInput.value.trim();

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
  formData.append('user_input', messageContent);
  formData.append('model_select', document.getElementById('model_select').value);

  const conversationHistory = JSON.parse(document.getElementById('conversation_history').value);
  conversationHistory.push({ role: 'user', content: messageContent });
  document.getElementById('conversation_history').value = JSON.stringify(conversationHistory);

  appendMessage(messageContent, false);
  userInput.value = '';
  
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
  }).catch(error => {
    console.error('Error:', error);
    finishAssistantMessage('Error: Could not get response from server.');
  });
}

function streamResponse(reader) {
  let contentBuffer = '';
  const decoder = new TextDecoder();

  function processText({ done, value }) {
    if (done) {
      finishAssistantMessage(contentBuffer);
      return;
    }

    const chunk = decoder.decode(value, { stream: true });
    contentBuffer += chunk;

    if (!window.updateTimeout) {
      window.updateTimeout = setTimeout(() => {
        updateAssistantMessage(contentBuffer);
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
  contentDiv.className = 'message-content';

  if (isAssistant) {
    contentDiv.innerHTML = marked.parse(content);
    applyHighlightingAndCopyButtons();
  } else {
    contentDiv.textContent = content;
  }

  messageDiv.appendChild(contentDiv);
  chatArea.appendChild(messageDiv);
  scrollToBottom();
}

function createAssistantMessage() {
  const chatArea = document.getElementById("chat_area");
  const assistantMessage = document.createElement('div');
  assistantMessage.className = 'message assistant-message typing-animation';
  chatArea.appendChild(assistantMessage);
  scrollToBottom();
  return assistantMessage;
}

function updateAssistantMessage(content) {
  const assistantMessage = document.querySelector('.assistant-message.typing-animation');
  if (assistantMessage) {
    assistantMessage.innerHTML = marked.parse(content);
    applyHighlightingAndCopyButtons();
    scrollToBottom();
  }
}

function finishAssistantMessage(content) {
  const assistantMessage = document.querySelector('.assistant-message.typing-animation');
  if (assistantMessage) {
    assistantMessage.classList.remove('typing-animation');
    assistantMessage.innerHTML = marked.parse(content);
    applyHighlightingAndCopyButtons();
    scrollToBottom();

    const conversationHistory = JSON.parse(document.getElementById('conversation_history').value);
    conversationHistory.push({ role: 'assistant', content: content });
    document.getElementById('conversation_history').value = JSON.stringify(conversationHistory);
  }
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
  assistantPromptWrapper.style.display = assistantPromptWrapper.style.display === 'none' ? 'block' : 'none';
}

function handleModelChange() {
  console.log('Model changed to:', this.value);
}

function applyHighlightingAndCopyButtons() {
  document.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
  });

  document.querySelectorAll('pre').forEach((pre) => {
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

// Initialize
attachEventListeners();
adjustChatAreaHeight();
