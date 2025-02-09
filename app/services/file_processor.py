from typing import List
import PyPDF2
import io
import cohere
import numpy as np

def smart_chunking(text: str, chunk_size: int = 1500, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks intelligently at sentence boundaries.
    
    Args:
        text: Text to be chunked
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    def find_sentence_boundary(text: str, position: int) -> int:
        """Find the next sentence boundary after the given position."""
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

def extract_text_from_pdf(file: io.BytesIO) -> List[str]:
    """
    Extract text from PDF file and split into chunks.
    
    Args:
        file: PDF file in BytesIO format
    
    Returns:
        List of text chunks from the PDF
    """
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    
    chunks = smart_chunking(text)
    return chunks

def batch_embed(texts: List[str], 
               cohere_client: cohere.Client,
               max_batch_size: int = 95) -> List[np.ndarray]:
    """
    Generate embeddings for text chunks in batches.
    
    Args:
        texts: List of text chunks to embed
        cohere_client: Initialized Cohere client
        max_batch_size: Maximum number of texts to process in one batch
    
    Returns:
        List of embeddings as numpy arrays
    """
    all_embeddings = []
    
    for i in range(0, len(texts), max_batch_size):
        batch = texts[i:i + max_batch_size]
        batch_embeddings = cohere_client.embed(
            texts=batch,
            model='embed-multilingual-v3.0',
            input_type='search_document'
        ).embeddings
        all_embeddings.extend(batch_embeddings)
    
    return all_embeddings
