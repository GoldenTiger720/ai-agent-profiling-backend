import re
from bs4 import BeautifulSoup
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def clean_html(html_content: str) -> str:
    """
    Clean HTML content and extract only text.
    
    Args:
        html_content: Raw HTML content as string
        
    Returns:
        Cleaned text content
    """
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(['script', 'style', 'meta', 'noscript', 'header', 'footer', 'nav']):
            script_or_style.decompose()
        
        # Get text
        text = soup.get_text(separator=' ')
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        # Return original text if cleaning fails
        return html_content

def remove_duplicates(text: str) -> str:
    """
    Remove duplicate paragraphs or sentences from text.
    
    Args:
        text: Text content with potential duplicates
    
    Returns:
        Text with duplicates removed
    """
    # Split text into paragraphs
    paragraphs = text.split('\n')
    
    # Remove empty paragraphs and strip whitespace
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    # Remove duplicate paragraphs while preserving order
    unique_paragraphs = []
    seen_paragraphs = set()
    
    for p in paragraphs:
        if p not in seen_paragraphs:
            unique_paragraphs.append(p)
            seen_paragraphs.add(p)
    
    # Join paragraphs back into text
    return '\n'.join(unique_paragraphs)

def clean_text(text: str) -> str:
    """
    Clean text by removing unwanted characters and formatting.
    
    Args:
        text: Raw text input
        
    Returns:
        Cleaned text
    """
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-\'"]', ' ', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def chunk_text(text: str, max_tokens: int = None) -> list:
    """
    Split text into chunks that respect the token limit for OpenAI API.
    Simple approximation: 1 token ≈ 4 characters for English text.
    
    Args:
        text: Text to split into chunks
        max_tokens: Maximum tokens per chunk (default: from settings)
        
    Returns:
        List of text chunks
    """
    if max_tokens is None:
        max_tokens = settings.MAX_TOKENS_PER_REQUEST
    
    # Approximate characters per token
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    
    # If text is already short enough, return it as is
    if len(text) <= max_chars:
        return [text]
    
    # Split text into paragraphs
    paragraphs = text.split('\n')
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the limit, start a new chunk
        if len(current_chunk) + len(paragraph) > max_chars:
            # If the current chunk has content, add it to chunks
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Start a new chunk with this paragraph
            current_chunk = paragraph + "\n"
        else:
            # Add paragraph to the current chunk
            current_chunk += paragraph + "\n"
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def process_text_for_ai(raw_text: str) -> list:
    """
    Process raw text to prepare it for input to OpenAI API.
    
    Args:
        raw_text: Raw text from various sources
        
    Returns:
        List of clean text chunks ready for API input
    """
    # Clean HTML if present
    if "<html" in raw_text.lower() or "<body" in raw_text.lower():
        text = clean_html(raw_text)
    else:
        text = raw_text
    
    # Clean the text
    cleaned_text = clean_text(text)
    
    # Remove duplicates
    deduplicated_text = remove_duplicates(cleaned_text)
    
    # Split into chunks
    chunks = chunk_text(deduplicated_text)
    
    return chunks