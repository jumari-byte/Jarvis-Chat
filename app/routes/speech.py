from flask import Blueprint, request, jsonify, send_file, current_app
import os
import tempfile
import edge_tts
from ..utils.logging import log_chat

speech_bp = Blueprint('speech', __name__)

def run_async(coro):
    """
    Helper function to run async code in Flask.
    
    Args:
        coro: Coroutine to execute
    
    Returns:
        Result of the coroutine execution
    """
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@speech_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Handle audio transcription requests."""
    model_manager = current_app.model_manager
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if audio_file:
        try:
            # Ensure upload directory exists
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
            
            # Save audio file temporarily
            temp_audio_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                'temp_audio.wav'
            )
            audio_file.save(temp_audio_path)
            
            try:
                # Use Groq client for transcription
                client = model_manager.get_client_for_model('whisper-large-v3')
                with open(temp_audio_path, 'rb') as audio:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=audio,
                        language="id",
                        response_format="text"
                    )
                
                return jsonify({'transcript': transcript})
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                    
        except Exception as e:
            log_chat("Audio transcription", "whisper-large-v3", False, str(e))
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid audio file'}), 400

@speech_bp.route('/tts', methods=['POST'])
def text_to_speech():
    """Handle text-to-speech requests."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        text = data.get('text', '')
        language = data.get('language', 'en-US')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Get voice mapping from config
        voice_mapping = current_app.config['VOICE_MAPPING']
        voice = voice_mapping.get(language, 'en-US-ChristopherNeural')
        
        # TTS Parameters
        RATE = "+17%"  # 17% faster
        PITCH = "-10Hz"  # 10Hz lower pitch
        
        # Create temporary directory and file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'tts_audio.mp3')
        
        try:
            # Generate audio file
            async def generate_audio():
                communicate = edge_tts.Communicate(
                    text,
                    voice,
                    rate=RATE,
                    pitch=PITCH
                )
                await communicate.save(temp_path)
            
            # Run async code
            run_async(generate_audio())
            
            # Send file and clean up afterward
            return send_file(
                temp_path,
                mimetype='audio/mpeg',
                as_attachment=True,
                download_name='tts_audio.mp3'
            )
            
        except Exception as e:
            log_chat("Text-to-speech", voice, False, str(e))
            return jsonify({'error': str(e)}), 500
            
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                current_app.logger.error(
                    f"Error cleaning up temp files: {str(e)}"
                )
                
    except Exception as e:
        log_chat("Text-to-speech", "N/A", False, str(e))
        return jsonify({'error': str(e)}), 500
