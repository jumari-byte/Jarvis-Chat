from flask import Blueprint, request, render_template, jsonify, session, current_app, g, redirect, url_for
import os
import io
import base64
from werkzeug.utils import secure_filename
import PyPDF2
import numpy as np
import faiss

from ..core.session import SessionData
from ..services.file_processor import extract_text_from_pdf, batch_embed
from ..utils.logging import log_chat

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Handle index route and file uploads."""
    session_manager = current_app.session_manager
    cohere_client = g.cohere_client
    
    # Get or create session
    session_id = session.get('session_id')
    if not session_id or not session_manager.get_session(session_id):
        session_id = session_manager.create_session()
        session['session_id'] = session_id
    
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({
                'message': 'No file provided',
                'pdf_context_available': False,
                'image_context_available': False
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'message': 'No selected file',
                'pdf_context_available': False,
                'image_context_available': False
            }), 400
        
        if not file or not current_app.config.get('ALLOWED_EXTENSIONS') or \
           not file.filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']:
            return jsonify({
                'message': 'Invalid file type. Please upload a PDF or an image.',
                'pdf_context_available': False,
                'image_context_available': False
            }), 400
        
        filename = secure_filename(file.filename)
        file_content = file.read()
        
        try:
            if filename.lower().endswith('.pdf'):
                # Process PDF file
                chunks = extract_text_from_pdf(io.BytesIO(file_content))
                
                # Create FAISS index
                chunk_embeddings = batch_embed(chunks, cohere_client)
                embeddings_array = np.array(chunk_embeddings)
                dimension = embeddings_array.shape[1]
                index = faiss.IndexFlatIP(dimension)
                index.add(embeddings_array)
                
                # Update session with PDF data
                session_manager.update_session_data(
                    session_id,
                    pdf_chunks=chunks,
                    faiss_index=index,
                    embeddings=embeddings_array
                )
                
                return jsonify({
                    'message': "PDF uploaded and processed successfully. "
                              "You can now chat with me, and I'll respond based on "
                              "the context of your document",
                    'pdf_context_available': True,
                    'image_context_available': False
                })
                
            elif filename.lower().endswith(('.jpg', '.png', '.jpeg')):
                # Process image file
                base64_image = base64.b64encode(file_content).decode('utf-8')
                
                # Update session with image data
                session_manager.update_session_data(
                    session_id,
                    image_base64=base64_image
                )
                
                return jsonify({
                    'message': "Image uploaded successfully. "
                              "You can now ask questions about the image.",
                    'pdf_context_available': False,
                    'image_context_available': True
                })
                
        except Exception as e:
            log_chat("File upload", "N/A", False, str(e))
            return jsonify({
                'message': f'Error processing file: {str(e)}',
                'pdf_context_available': False,
                'image_context_available': False
            }), 500
    
    # GET request - render template
    return render_template(
        'index.html',
        conversation=session_data.conversation,
        assistant_prompt=session_data.assistant_prompt,
        selected_model=session_data.selected_model,
        pdf_context_available=bool(session_data.pdf_chunks),
        image_context_available=bool(session_data.image_base64),
        audio_input_enabled=True
    )

@main_bp.route('/reset', methods=['POST'])
def reset():
    """Reset session data and redirect to index."""
    session_manager = current_app.session_manager
    
    # Clear session data
    session_id = session.get('session_id')
    if session_id:
        session_manager.clear_session(session_id)
    session.clear()
    
    # Redirect to index page
    return redirect(url_for('main.index'))