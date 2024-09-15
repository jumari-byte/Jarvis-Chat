# Jarvis-chat
A Lightweight Frontend for [the groq API](https://console.groq.com/docs/quickstart).

**Overview**
Jarvis-chat is a simple and lightweight frontend interface for the Groq API. It provides a basic memory for follow-up questions, customizable system prompts, and the ability to choose from various AI models. This project is designed to be easy to use and requires minimal setup.

**Features**
- **Rudimentary Memory**: Groq-Frontend has a basic memory that allows it to remember previous conversations and respond accordingly.
- **Customizable System Prompt**: You can customize the system prompt to fit your specific needs.
- **Choose AI Model**: Select from a variety of AI models to use with the Groq API.
- **Session Reset**: Easily reset the session to start a new conversation.
- **Markdown Rendering**: Supports rendering of Markdown syntax for formatted text.
- **Code Highlighting**: Highlights code snippets with syntax highlighting for better readability.
- **Code Copying**: Allows users to easily copy generated code with a single click.
- **Web Search Function**: You can perform a web search to get up-to-date information.



[**Live Demo**](https://ai.arjum.com/)

**Requirements** 

To use Jarvis-chat, you'll need to install the following dependencies:
```
pip install flask groq
```

**Getting Started**
- Clone the repository or download the code.
- Set your GROQ_API_KEY environment variable. You can obtain an API key [here](https://console.groq.com/keys).
- Run the application using:
```
python app.py
```
Open a web browser and navigate to http://localhost:4001

To adjust the rendering speed of content, you can modify the smoothRender function in the script.js file
```
function smoothRender(content, renderInterval = 17) {
  let renderIndex = 0;
  const renderStep = 3; // Number of characters to render in each step
```

**Web search Function**

To perform a web search, you can type the word "search" or "cari," and Jarvis will use the top 2 search results as context to provide a response.

You can also get information from a URL. Jarvis will add the content from the URL as context before providing a response.

thats it.
