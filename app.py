from flask import Flask, request, render_template, session, redirect, url_for, Response, stream_with_context, jsonify
import os
import json
import io
import uuid
import re 
import openai
from tools.WebSearch_Tool import WebSearch_Tool
from tools.WebGetContents_Tool import WebGetContents_Tool
from werkzeug.utils import secure_filename
import PyPDF2
import cohere
import faiss
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Initialize clients for different endpoints
client_cerebras = openai.OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=os.environ.get("CEREBRAS_API_KEY")
)

client_groq = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

client_mistral = openai.OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("MISTRAL_API_KEY")
)

client_sambanova = openai.OpenAI(
    base_url="https://api.sambanova.ai/v1",
    api_key=os.environ.get("SAMBANOVA_API_KEY")
)

# Initialize Cohere client
cohere_client = cohere.Client(os.environ.get("COHERE_API_KEY"))

# Mapping of models to clients
model_client_mapping = {
    'llama3.1-70b': client_cerebras,
    'llama3.1-8b': client_cerebras,
    'mistral-large-2407': client_mistral,
    'mistral-small-2409': client_mistral,
    'Meta-Llama-3.1-405B-Instruct': client_sambanova,
    # Add more models and their corresponding clients here
}

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def smart_chunking(text, chunk_size=1500, overlap=100):
    chunks = []
    start = 0
    
    def find_sentence_boundary(text, position):
        next_period = text.find('.', position)
        next_newline = text.find('\n', position)
        if next_period == -1 and next_newline == -1:
            return len(text)
        elif next_period == -1:
            return next_newline
        elif next_newline == -1:
            return next_period
        else:
            return min(next_period, next_newline) + 1

    while start < len(text):
        end = start + chunk_size
        if end > len(text):
            end = len(text)
        else:
            end = find_sentence_boundary(text, end)
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = max(start + chunk_size - overlap, end - overlap)
    
    return chunks

def semantic_search(query, chunks, index, embeddings, k=3):
    query_embedding = cohere_client.embed(texts=[query], model='embed-multilingual-v3.0', input_type='search_query').embeddings[0]
    _, I = index.search(np.array([query_embedding]), k)
    return [
        {"chunk": chunks[i], "score": float(np.dot(embeddings[i], query_embedding))}
        for i in I[0]
    ]

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    
    chunks = smart_chunking(text)
    return chunks

def batch_embed(texts, max_batch_size=95):
    all_embeddings = []
    for i in range(0, len(texts), max_batch_size):
        batch = texts[i:i+max_batch_size]
        batch_embeddings = cohere_client.embed(texts=batch, model='embed-multilingual-v3.0', input_type='search_document').embeddings
        all_embeddings.extend(batch_embeddings)
    return all_embeddings

def web_search(query):
    search_results = WebSearch_Tool(query)
    if len(search_results) >= 2:
        for i in range(2):
            url = search_results[i]['url']
            content = WebGetContents_Tool(url)
            if content:
                search_results[i]['content'] = content[:8000]  # Limit content to 8000 characters
    return search_results[:2]  # Return only the top 2 results

# Add a simple in-memory storage for session data
session_storage = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        session_storage[session_id] = {
            'conversation': [],
            'assistant_prompt': 'You are Jarvis (Jumari Advanced Virtual Intelligence System). You are designed to assist users with a wide range of questions and tasks. You must provide answers that are easy to understand, simple, on point and accurate. Ensure that your answers are relevant to the context and do not contain incorrect information. You will interact with users in a polite and friendly manner, using proper language. You should analyze the question first and then fulfill users request to the best of your ability.',
            'selected_model': 'llama-3.1-70b-versatile',
            'pdf_chunks': [],
            'faiss_index': None,
            'embeddings': None
        }

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_content = file.read()
                chunks = extract_text_from_pdf(io.BytesIO(file_content))
                
                # Create FAISS index
                chunk_embeddings = batch_embed(chunks, max_batch_size=95)
                embeddings_array = np.array(chunk_embeddings)
                dimension = embeddings_array.shape[1]
                index = faiss.IndexFlatIP(dimension)
                index.add(embeddings_array)
                
                session_storage[session_id]['pdf_chunks'] = chunks
                session_storage[session_id]['faiss_index'] = index
                session_storage[session_id]['embeddings'] = embeddings_array
                
                return jsonify({
                    'message': "PDF uploaded and processed successfully. You can now chat with me, and I'll respond based on the context of your document",
                    'pdf_context_available': True
                })
            else:
                return jsonify({
                    'message': 'Invalid file type. Please upload a PDF.',
                    'pdf_context_available': False
                }), 400

    return render_template('index.html', 
                           conversation=session_storage[session_id]['conversation'], 
                           assistant_prompt=session_storage[session_id]['assistant_prompt'],
                           selected_model=session_storage[session_id]['selected_model'],
                           pdf_context_available=bool(session_storage[session_id]['pdf_chunks']))

@app.route('/stream', methods=['POST'])
def stream():
    session_id = session.get('session_id')
    user_input = request.form['user_input']
    assistant_prompt = request.form.get('assistant_prompt', '')
    selected_model = request.form.get('model_select', 'llama-3.1-70b-versatile')
    
    conversation_history = session_storage[session_id]['conversation']

    if assistant_prompt and not any(msg['role'] == 'system' and msg['content'] == assistant_prompt for msg in conversation_history):
        assistant_message = {"role": "system", "content": assistant_prompt}
        conversation_history.insert(0, assistant_message)

    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = url_pattern.findall(user_input)

    if urls:
        for url in urls:
            web_content = WebGetContents_Tool(url)
            if web_content:
                url_content = f"Content from [URL: {url}]\n{web_content[:8000]}\n\n"
                conversation_history.append({
                    'role': 'system',
                    'content': f" {url_content}"
                })
                user_input = f"Use content from the : {url} to answer: {user_input}"

    if "search" in user_input.lower() or "cari" in user_input.lower():
        if "cari" in user_input.lower():
            query = user_input.lower().split("cari")[-1].strip()
        elif "search" in user_input.lower():
            query = user_input.lower().split("search")[-1].strip()
        search_results = web_search(query)
        search_content = f"Search results for '{query}':\n" + "\n".join([f"- {result['url']}: {result.get('content', 'No content available')}" for result in search_results])
        conversation_history.append({
            'role': 'system',
            'content': f" {search_content}"
        })
        user_input = f"Please use the search results to answer: {user_input}"

    if session_storage[session_id]['pdf_chunks'] and session_storage[session_id]['faiss_index'] and session_storage[session_id]['embeddings'] is not None:
        relevant_chunks = semantic_search(user_input, session_storage[session_id]['pdf_chunks'], session_storage[session_id]['faiss_index'], session_storage[session_id]['embeddings'], k=3)
        pdf_content = "Top 3 relevant PDF content:\n" + "\n".join([f"{i+1}. {chunk['chunk']} (Relevance: {chunk['score']:.2f})" for i, chunk in enumerate(relevant_chunks)])
        conversation_history.append({
            'role': 'system',
            'content': pdf_content
        })

    user_message = {"role": "user", "content": user_input}
    conversation_history.append(user_message)

    client = model_client_mapping.get(selected_model, client_groq)

    def generate():
        try:
            stream = client.chat.completions.create(
                messages=conversation_history,
                model=selected_model,
                stream=True,
                temperature=0.65,
            )
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content.encode('utf-8')

            conversation_history.append({"role": "assistant", "content": full_response})
            session_storage[session_id]['conversation'] = conversation_history
            session_storage[session_id]['assistant_prompt'] = assistant_prompt
            session_storage[session_id]['selected_model'] = selected_model
        except Exception as e:
            yield f"Error connecting to the model: {str(e)}".encode('utf-8')

    response = Response(stream_with_context(generate()), content_type='text/plain; charset=utf-8')
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/reset', methods=['POST'])
def reset():
    session_id = session.get('session_id')
    if session_id in session_storage:
        del session_storage[session_id]
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4001, debug=True)
