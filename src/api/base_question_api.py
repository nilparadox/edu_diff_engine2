from typing import List, Dict, Any
from abc import ABC, abstractmethod


class BaseQuestionAPI(ABC):
    """
    Abstract interface for external question generators.
    User can implement this with OpenAI, Groq, Gemini, local LLM, etc.
    """

    @abstractmethod
    def generate(self, messages: List[Dict[str, Any]]) -> str:
        """
        Takes a chat-like message list and returns the assistant content as string.
        """
        raise NotImplementedError
