from typing import Dict, Any, Optional, List
import uuid
import faiss
import numpy as np
from datetime import datetime

class SessionData:
    """Class to represent session data structure."""
    
    def __init__(self, 
                 assistant_prompt: str = "", 
                 selected_model: str = "mistral-small-latest"):  # Changed default model
        """
        Initialize a new session with default values.
        
        Args:
            assistant_prompt: Custom prompt for the assistant
            selected_model: Selected AI model (defaults to mistral-small-latest)
        """
        self.conversation: List[Dict[str, Any]] = []
        self.assistant_prompt: str = assistant_prompt or self._get_default_prompt()
        self.selected_model: str = selected_model
        self.pdf_chunks: List[str] = []
        self.faiss_index: Optional[faiss.IndexFlatIP] = None
        self.embeddings: Optional[np.ndarray] = None
        self.image_base64: Optional[str] = None
        self.created_at = datetime.now()

    @staticmethod
    def _get_default_prompt() -> str:
        """Get the default assistant prompt."""
        return (
            "You are Jarvis (Jumari Advanced Virtual Intelligence System). "
            "You are designed to assist users with a wide range of questions and tasks. "
            "You must provide answers that are easy to understand, simple, on point and accurate. "
            "Ensure that your answers are relevant to the context and do not contain incorrect information. "
            "You will interact with users in a polite and friendly manner. "
            "You should analyze the question first and then fulfill users request to the best of your ability."
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert session data to dictionary format."""
        return {
            'conversation': self.conversation,
            'assistant_prompt': self.assistant_prompt,
            'selected_model': self.selected_model,
            'pdf_chunks': self.pdf_chunks,
            'faiss_index': self.faiss_index,
            'embeddings': self.embeddings,
            'image_base64': self.image_base64
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create SessionData instance from dictionary."""
        session = cls(
            assistant_prompt=data.get('assistant_prompt', ''),
            selected_model=data.get('selected_model', 'mistral-small-latest')  # Default model
        )
        session.conversation = data.get('conversation', [])
        session.pdf_chunks = data.get('pdf_chunks', [])
        session.faiss_index = data.get('faiss_index')
        session.embeddings = data.get('embeddings')
        session.image_base64 = data.get('image_base64')
        return session

class SessionManager:
    """Manager class for handling session storage and operations."""
    
    def __init__(self):
        """Initialize session storage."""
        self._sessions: Dict[str, SessionData] = {}

    def create_session(self, 
                      assistant_prompt: str = "",
                      selected_model: str = "mistral-small-latest") -> str:  # Default model
        """
        Create a new session and return its ID.
        
        Args:
            assistant_prompt: Optional custom prompt
            selected_model: Optional model selection
            
        Returns:
            New session ID
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = SessionData(
            assistant_prompt=assistant_prompt,
            selected_model=selected_model
        )
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data for given session ID."""
        return self._sessions.get(session_id)

    def update_session(self, 
                      session_id: str, 
                      user_input: str, 
                      assistant_response: str,
                      assistant_prompt: Optional[str] = None,
                      selected_model: Optional[str] = None) -> None:
        """Update session with new conversation data."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session {session_id} not found")

        # Update conversation
        session.conversation.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": assistant_response}
        ])

        # Update other session attributes if provided
        if assistant_prompt:
            session.assistant_prompt = assistant_prompt
        if selected_model:
            session.selected_model = selected_model

    def update_session_data(self, 
                          session_id: str, 
                          pdf_chunks: Optional[List[str]] = None,
                          faiss_index: Optional[faiss.IndexFlatIP] = None,
                          embeddings: Optional[np.ndarray] = None,
                          image_base64: Optional[str] = None) -> None:
        """Update session with new data components."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session {session_id} not found")

        if pdf_chunks is not None:
            session.pdf_chunks = pdf_chunks
        if faiss_index is not None:
            session.faiss_index = faiss_index
        if embeddings is not None:
            session.embeddings = embeddings
        if image_base64 is not None:
            session.image_base64 = image_base64

    def clear_session(self, session_id: str) -> None:
        """Clear session data."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_conversation_context(self, 
                               session_id: str, 
                               with_system_prompt: bool = True) -> List[Dict[str, Any]]:
        """Get conversation history with optional system prompt."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session {session_id} not found")

        context = []
        if with_system_prompt:
            today = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M")
            context.append({
                "role": "system",
                "content": f"{session.assistant_prompt}\nToday's date is {today}\nCurrent time is {current_time}"
            })

        context.extend(session.conversation)
        return context

    def has_pdf_context(self, session_id: str) -> bool:
        """Check if session has PDF context available."""
        session = self.get_session(session_id)
        return bool(session and session.pdf_chunks)

    def has_image_context(self, session_id: str) -> bool:
        """Check if session has image context available."""
        session = self.get_session(session_id)
        return bool(session and session.image_base64)

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> None:
        """Remove sessions older than specified hours."""
        from datetime import datetime, timedelta
        now = datetime.now()
        expired_sessions = []
        for session_id, session in self._sessions.items():
            try:
                created_at = session.created_at
            except AttributeError:
                expired_sessions.append(session_id)
                continue
            if now - created_at > timedelta(hours=max_age_hours):
                expired_sessions.append(session_id)
        for session_id in expired_sessions:
            try:
                del self._sessions[session_id]
            except Exception:
                pass