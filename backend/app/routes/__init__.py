"""Routes package initialization."""
from .assistant import assistant_bp
from .resume import resume_bp

__all__ = ['resume_bp', 'assistant_bp']
