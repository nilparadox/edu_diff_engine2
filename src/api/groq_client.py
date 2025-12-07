from dotenv import load_dotenv
load_dotenv()
from typing import List, Dict, Any
from groq import Groq
from ..config import get_groq_internal_key


class GroqRubricClient:
    """
    Internal Groq client.
    Used to:
      - read PDF context
      - generate dynamic rubrics for difficulty levels
    """

    def __init__(self, model: str | None = None):
        api_key = get_groq_internal_key()
        self.client = Groq(api_key=api_key)
        # Fast, cheap model for meta tasks
        self.model = model or "llama-3.1-8b-instant"

    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Simple chat completion wrapper.
        Returns the content of the first choice.
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return completion.choices[0].message.content
