from typing import List, Dict, Any
import json

from openai import OpenAI

from .base_question_api import BaseQuestionAPI


class OpenAIQuestionAPI(BaseQuestionAPI):
    """
    External question generator using OpenAI.

    IMPORTANT:
    - This class NEVER reads environment variables.
    - You MUST pass api_key explicitly when you create it.
    - The library does not store or log your key; you control it.
    """

    def __init__(self, api_key: str, model: str | None = None):
        if not api_key:
            raise ValueError("OpenAIQuestionAPI: api_key must be provided explicitly.")

        # New OpenAI client
        self.client = OpenAI(api_key=api_key)

        # You can change this default model later
        self.model = model or "gpt-4.1-mini"

    def generate(self, messages: List[Dict[str, Any]]) -> str:
        """
        messages: chat-style messages (list of {role, content})
        Returns: the content string from the model (expected to be JSON).
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
        )
        content = completion.choices[0].message.content or ""
        content_stripped = content.strip()

        # If model behaves perfectly and returns pure JSON
        if content_stripped.startswith("{") and content_stripped.endswith("}"):
            return content_stripped

        # Try to salvage JSON if there's extra text
        try:
            cleaned = content_stripped[
                content_stripped.find("{") : content_stripped.rfind("}") + 1
            ]
            json.loads(cleaned)  # validate
            return cleaned
        except Exception:
            # Last resort: return raw; the engine will raise if json.loads fails.
            return content_stripped
