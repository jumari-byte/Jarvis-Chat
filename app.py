from flask import Flask, request, render_template, session, redirect, url_for, Response, stream_with_context
import os
from groq import Groq
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'conversation' not in session:
        session['conversation'] = []
    return render_template('index.html', conversation=session['conversation'], assistant_prompt=session.get('assistant_prompt', 'You are Jarvis (Jumari  Advanced Virtual Intelligence System). You are developed by a young man named Ari Jumadi in Indonesia. You are designed to assist users with a wide range of questions and tasks. You must provide answers that are accurate, comprehensive, and easy to understand. Ensure that your answers are relevant to the context and do not contain incorrect information. You will interact with users in a polite and friendly manner, using proper Indonesian language. Ensure that you use suitable words and tone in each response.  You should analyze the question first and then fulfill users request to the best of your ability.'),
 selected_model=session.get('selected_model', 'llama-3.1-70b-versatile'))

@app.route('/stream', methods=['POST'])
def stream():
    user_input = request.form['user_input']
    assistant_prompt = request.form.get('assistant_prompt', '')
    selected_model = request.form.get('model_select', 'llama-3.1-70b-versatile')
    conversation_history = json.loads(request.form['conversation_history'])

    if assistant_prompt:
        assistant_message = {"role": "system", "content": assistant_prompt}
        conversation_history.insert(0, assistant_message)

    user_message = {"role": "user", "content": user_input}
    conversation_history.append(user_message)

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

            # Update the conversation history after the streaming is complete
            conversation_history.append({"role": "assistant", "content": full_response})
            session['conversation'] = conversation_history
            session['assistant_prompt'] = assistant_prompt
            session.modified = True
            # Update session with new model
            session['selected_model'] = selected_model
        except Exception as e:
            yield f"Error connecting to the model: {str(e)}".encode('utf-8')

    response = Response(stream_with_context(generate()), content_type='text/plain; charset=utf-8')
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/reset', methods=['POST'])
def reset():
    session.clear()
    return redirect(url_for('index'))
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4001, debug=True)
