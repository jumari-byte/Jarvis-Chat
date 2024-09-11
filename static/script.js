document.getElementById("user_input").focus();
const chatArea = document.getElementById("chat_area");
const queryForm = document.getElementById("query-form");
const userInput = document.getElementById("user_input");
const sendButton = document.getElementById("send-button");
const assistantPrompt = document.getElementById("assistant_prompt");
const settingsButton = document.getElementById('settings-button');
const assistantPromptWrapper = document.getElementById('assistant-prompt-wrapper');

let currentAssistantMessage;
let contentBuffer = '';
const decoder = new TextDecoder();

function adjustChatAreaHeight() {
  const inputWrapper = document.querySelector('.input-wrapper');
  const inputHeight = inputWrapper.offsetHeight;
  const chatArea = document.getElementById('chat_area');
  chatArea.style.maxHeight = `calc(100vh - ${inputHeight + 100}px)`;
}

window.addEventListener('load', adjustChatAreaHeight);
window.addEventListener('resize', adjustChatAreaHeight);

function addCopyButtons() {
  document.querySelectorAll('pre').forEach((pre) => {
    if (!pre.querySelector('.copy-button')) {
      const button = document.createElement('button');
      button.className = 'copy-button';
      button.textContent = 'Copy';
      button.type = 'button';
      button.addEventListener('click', (event) => {
        event.preventDefault();
        const code = pre.querySelector('code');
        navigator.clipboard.writeText(code.textContent).then(() => {
          button.textContent = 'Copied!';
          setTimeout(() => {
            button.textContent = 'Copy';
          }, 2000);
        }).catch((error) => {
          console.error('Failed to copy: ', error);
          button.textContent = 'Error';
        });
      });
      pre.appendChild(button);
    }
  });
}

function applyHighlighting() {
  document.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
  });
}

function renderMessage(content, isAssistant) {
  const messageDiv = document.createElement('div');
  messageDiv.className = isAssistant ? 'message assistant-message' : 'message user-message';

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';

  if (isAssistant) {
    contentDiv.innerHTML = marked.parse(content);
    applyHighlighting();
    addCopyButtons();
  } else {
    contentDiv.textContent = content;
  }

  messageDiv.appendChild(contentDiv);
  return messageDiv;
}

function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

function createAssistantMessage() {
  currentAssistantMessage = document.createElement('div');
  currentAssistantMessage.className = 'message assistant-message typing-animation';
  currentAssistantMessage.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  chatArea.appendChild(currentAssistantMessage);
  scrollToBottom();
}

function updateAssistantMessage(content) {
  if (currentAssistantMessage) {
    currentAssistantMessage.innerHTML = marked.parse(content) + '<span class="cursor">▋</span>';
    applyHighlighting();
    addCopyButtons();
    scrollToBottom();
  }
}

function finishAssistantMessage(content) {
  if (currentAssistantMessage) {
    currentAssistantMessage.innerHTML = marked.parse(content);
    applyHighlighting();
    addCopyButtons();

    const conversationHistory = JSON.parse(document.getElementById('conversation_history').value);
    conversationHistory.push({ role: 'assistant', content: content });
    document.getElementById('conversation_history').value = JSON.stringify(conversationHistory);

    currentAssistantMessage = null;
    contentBuffer = '';
  }
}

function smoothRender(content, renderInterval = 17) {
  let renderIndex = 0;
  const renderStep = 3; // Number of characters to render in each step

  function renderNextChunk() {
    if (renderIndex === 0) {
      // Remove typing animation when starting to render content
      currentAssistantMessage.classList.remove('typing-animation');
      currentAssistantMessage.innerHTML = '';
    }

    if (renderIndex < content.length) {
      const chunk = content.slice(renderIndex, renderIndex + renderStep);
      updateAssistantMessage(content.slice(0, renderIndex + renderStep));
      renderIndex += renderStep;
      setTimeout(renderNextChunk, renderInterval);
    } else {
      finishAssistantMessage(content);
    }
  }

  renderNextChunk();
}

function sendMessage(event) {
  event.preventDefault();
  const formData = new FormData(queryForm);
  const userInputValue = userInput.value.trim();

  if (userInputValue === '') {
    alert('Please enter a message');
    return;
  }

   // Add user input and selected model to formData
  formData.append('user_input', userInputValue);
  formData.append('model_select', modelSelect.value);

  const conversationHistory = JSON.parse(document.getElementById('conversation_history').value);
  conversationHistory.push({ role: 'user', content: userInputValue });
  document.getElementById('conversation_history').value = JSON.stringify(conversationHistory);

  chatArea.appendChild(renderMessage(userInput.value, false));
  userInput.value = '';

  createAssistantMessage();
  adjustChatAreaHeight();
  scrollToBottom();

  fetch('/stream', {
    method: 'POST',
    body: formData
  }).then(response => {
    const reader = response.body.getReader();

    function processText(result) {
      if (result.done) {
        smoothRender(contentBuffer);
        return;
      }

      const chunk = decoder.decode(result.value, { stream: true });
      contentBuffer += chunk;

      return reader.read().then(processText);
    }

    return reader.read().then(processText);
  }).catch(error => {
    console.error('Error:', error);
    finishAssistantMessage('Error: Could not get response from server.');
  });
}

sendButton.addEventListener("click", sendMessage);

userInput.addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = (this.scrollHeight) + 'px';
  adjustChatAreaHeight();
});

chatArea.scrollTop = chatArea.scrollHeight;

document.querySelectorAll('.message').forEach(message => {
  if (message.classList.contains('assistant-message')) {
    const content = message.textContent;
    message.innerHTML = '';
    message.appendChild(renderMessage(content, true).firstChild);
  }
});

document.addEventListener('DOMContentLoaded', (event) => {
  applyHighlighting();
  addCopyButtons();
});

settingsButton.addEventListener('click', function() {
  if (assistantPromptWrapper.style.display === 'none') {
    assistantPromptWrapper.style.display = 'block';
  } else {
    assistantPromptWrapper.style.display = 'none';
  }
});
