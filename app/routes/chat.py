from flask import Blueprint, request, Response, stream_with_context, current_app, g, session
import re
from typing import Generator, Dict, Any, List

from ..services.search import SearchService
from ..utils.logging import log_chat

chat_bp = Blueprint('chat', __name__)

def generate_chat_response(
    user_input: str,
    assistant_prompt: str,
    selected_model: str,
    session_id: str,
    disable_search: bool = False
) -> Generator[bytes, None, None]:
    """
    Generate streaming chat response.
    
    Args:
        user_input: User's input message
        assistant_prompt: System prompt for the assistant
        selected_model: Selected AI model name
        session_id: Current session ID
        disable_search: Whether to disable web search
    
    Yields:
        Chunks of response text encoded as bytes
    """
    session_manager = current_app.session_manager
    model_manager = current_app.model_manager
    cohere_client = g.cohere_client
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        yield b"Error: Session not found"
        return
    
    # Create temporary conversation history
    conversation_history = session_data.conversation.copy()
    conversation_history.append({"role": "user", "content": user_input})
    
    # Initialize variables for additional context
    url_content = ""
    search_content = ""
    pdf_content = ""
    image_content = None
    
    # Process URLs in user input
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    urls = url_pattern.findall(user_input)
    if urls:
        from tools.get_url_contents import get_url_contents
        for url in urls:
            web_content = get_url_contents(url)
            if web_content:
                url_content += f"Content from [URL: {url}]\n{web_content[:8000]}\n\n"
    
    # Handle web search if needed
    search_service = SearchService(model_manager.get_search_client())
    need_search, search_query = search_service.agent_search_decision(
        conversation_history,
        disable_search
    )
    
    if need_search:
        yield "SEARCH_MODE\n".encode('utf-8')
        search_results = search_service.web_search(search_query)
        search_content = (
            f"Search results for '{search_query}':\n" +
            "\n".join([
                f"- {result['url']}: {result.get('content', 'No content available')}"
                for result in search_results
            ])
        )
    
    # Process PDF content if available
    if session_data.pdf_chunks and session_data.faiss_index is not None:
        # Perform semantic search
        relevant_chunks = semantic_search(
            user_input,
            session_data.pdf_chunks,
            session_data.faiss_index,
            session_data.embeddings,
            cohere_client,
            k=3
        )
        pdf_content = "Top 3 relevant PDF content:\n" + "\n".join([
            f"{i+1}. {chunk['chunk']} (Relevance: {chunk['score']:.2f})"
            for i, chunk in enumerate(relevant_chunks)
        ])
    
    # Process image content if available
    if session_data.image_base64:
        image_content = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{session_data.image_base64}"
            }
        }
        # Clear the image from session after using it
        session_manager.update_session_data(session_id, image_base64=None)
    
    # Construct the final conversation history
    final_history: List[Dict[str, Any]] = []
    
    # Add system prompt if provided
    if assistant_prompt:
        final_history.append({
            "role": "system",
            "content": assistant_prompt
        })
    
    # Add context information
    role = "assistant" if selected_model == 'gemini-2.0-flash-exp' else "system"
    if url_content:
        final_history.append({"role": role, "content": url_content})
    if search_content:
        final_history.append({"role": role, "content": search_content})
    if pdf_content:
        final_history.append({"role": role, "content": pdf_content})
    if url_content or search_content or pdf_content:
        final_history.append({
            "role": role,
            "content": "Add the information above to your knowledge."
        })
    
    # Add conversation history
    final_history.extend(conversation_history)
    
    # Prepare user input with potential image
    user_input_content = {
        "type": "text",
        "text": user_input
    }
    
    if image_content:
        final_history.append({
            "role": "user",
            "content": [user_input_content, image_content]
        })
    else:
        final_history.append({
            "role": "user",
            "content": [user_input_content]
        })
    
    # Get appropriate client for the selected model
    client = model_manager.get_client_for_model(selected_model)
    
    # Log chat information
    log_chat(user_input, selected_model, need_search)
    
    try:
        # Generate streaming response
        stream = client.chat.completions.create(
            messages=final_history,
            model=selected_model,
            stream=True,
            temperature=0.55,
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content.encode('utf-8')
        
        # Update conversation history after successful response
        session_manager.update_session(
            session_id,
            user_input,
            full_response,
            assistant_prompt,
            selected_model
        )
        
    except Exception as e:
        error_msg = f"Error connecting to the model: {str(e)}"
        log_chat(user_input, selected_model, need_search, error_msg)
        yield error_msg.encode('utf-8')

@chat_bp.route('/stream', methods=['POST'])
def stream():
    """Handle chat stream endpoint."""
    if not request.form.get('user_input'):
        return Response(
            "No user input provided",
            status=400,
            content_type='text/plain'
        )
    
    # Get parameters from request
    user_input = request.form['user_input']
    assistant_prompt = request.form.get('assistant_prompt', '')
    selected_model = request.form.get('model_select', 'mistral-small-latest')
    disable_search = request.form.get('disable_search', 'false').lower() == 'true'
    
    # Get session ID from Flask session
    session_id = session.get('session_id')
    if not session_id:
        # Create new session if one doesn't exist
        session_id = current_app.session_manager.create_session()
        session['session_id'] = session_id
    
    # Create response with streaming content
    response = Response(
        stream_with_context(
            generate_chat_response(
                user_input,
                assistant_prompt,
                selected_model,
                session_id,
                disable_search
            )
        ),
        content_type='text/plain; charset=utf-8'
    )
    
    # Set response headers
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    
    return response

def semantic_search(query: str,
                   chunks: List[str],
                   index: Any,
                   embeddings: Any,
                   cohere_client: Any,
                   k: int = 3) -> List[Dict[str, Any]]:
    """
    Perform semantic search on text chunks.
    
    Args:
        query: Search query
        chunks: List of text chunks to search
        index: FAISS index
        embeddings: Precomputed embeddings
        cohere_client: Initialized Cohere client
        k: Number of results to return
    
    Returns:
        List of dictionaries containing chunks and their relevance scores
    """
    import numpy as np
    embed_response = cohere_client.embed(
        texts=[query],
        model='embed-multilingual-v3.0',
        input_type='search_query'
    )
    # Get embeddings from Cohere response
    query_embedding = np.array(embed_response.embeddings[0])
    _, I = index.search(np.array(query_embedding).reshape(1, -1), k)
    
    return [
        {
            "chunk": chunks[i],
            "score": float(query_embedding.dot(embeddings[i]))
        }
        for i in I[0]
    ]