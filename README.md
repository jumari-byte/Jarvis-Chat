# Jarvis-chat
Jumari Advanced Virtual Intelligence System

**Overview**
Jarvis-Chat is a Flask-based web application that utilizes various AI models to provide users with a conversational interface for answering questions and completing tasks. It features basic memory for follow-up questions, customizable system prompts, and allows you to select from a variety of AI models. Designed for ease of use, it requires minimal setup to get started. Powering a local ChatGPT-like environment. The system is designed to be user-friendly, accurate, and informative, with a focus on providing relevant and contextual responses.

![jarvis](https://github.com/user-attachments/assets/fbe43765-def1-411c-9db1-97217794712a)

**Features**
- **Rudimentary Memory**: Groq-Frontend has a basic memory that allows it to remember previous conversations and respond accordingly.
- **Customizable System Prompt**: You can customize the system prompt to fit your specific needs.
- **Choose AI Model**: Select from a variety of AI models to use with the Groq, Cohere, Mistral, Cerebras, Sambanova API.
- **Session Reset**: Easily reset the session to start a new conversation.
- **Markdown Rendering**: Supports rendering of Markdown syntax for formatted text.
- **Code Highlighting**: Highlights code snippets with syntax highlighting for better readability.
- **Code Copying**: Allows users to easily copy generated code with a single click.
- **Web Search Function**: You can perform a web search to get up-to-date information.
- **PDF Document Support**: Upload PDF documents to JARVIS, which can then be used to provide context-specific responses.

[**Live Demo**](https://ai.arjum.com/)

**Requirements** 

To use Jarvis-chat, you'll need to install the following dependencies:
```
pip install flask groq beautifulsoup4 requests
```

**Getting Started**
- Clone the repository or download the code.
- cd to jarvis-chat
- Install the required dependencies using pip install -r requirements.txt
- Set up your API keys and credentials
- Run the application using:
```
python app.py
```
Open a web browser and navigate to http://localhost:4001

Example Use Cases

- General Knowledge: Ask JARVIS about general knowledge topics, such as history, science, or entertainment.
- PDF Document Analysis: Upload a PDF document and ask JARVIS to analyze its contents.
- Web Search: Ask JARVIS to search the web for information on a particular topic.


**Web search Function**

To perform a web search, you can type the word "search" or "cari," and Jarvis will use the top 2 search results as context to provide a response.

You can also get information from a URL. Jarvis will add the content from the URL as context before providing a response.


**Contributing**

We welcome contributions to JARVIS! If you're interested in adding new features or improving existing ones, please submit a pull request.

**License**

JARVIS is licensed under the MIT License.
