import json
from typing import List, Dict, Any
from .base_question_api import BaseQuestionAPI


class DummyQuestionAPI(BaseQuestionAPI):
    """
    Simple fake API for testing the pipeline.
    It ignores the prompt and returns a hard-coded JSON MCQ.
    """

    def generate(self, messages: List[Dict[str, Any]]) -> str:
        mcq = {
            "question_text": "This is a dummy question. Replace this API with a real LLM.",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D",
            ],
            "correct_option_index": 1,
            "explanation": "This is a placeholder explanation.",
        }
        return json.dumps(mcq)
