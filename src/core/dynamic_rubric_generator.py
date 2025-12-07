from __future__ import annotations

from typing import Literal
from pathlib import Path
import json

from pydantic import ValidationError

from ..utils.pdf_loader import PDFExtractor
from ..api.groq_client import GroqRubricClient
from .rubric_models import RubricSet


SubjectType = Literal[
    "physics", "math", "chemistry", "biology", "history", "english", "generic"
]


STATIC_SUBJECT_HINTS: dict[SubjectType, str] = {
    "physics": (
        "Difficulty usually increases with:\n"
        "- more steps of reasoning\n"
        "- combining multiple concepts or chapters\n"
        "- more symbolic/numerical manipulation\n"
        "- subtle conceptual traps or edge cases\n"
    ),
    "math": (
        "Difficulty usually increases with:\n"
        "- more algebraic / symbolic steps\n"
        "- non-obvious transformations or tricks\n"
        "- mixing multiple topics (e.g., algebra + geometry)\n"
    ),
    "history": (
        "Difficulty usually increases with:\n"
        "- deeper causal reasoning between events\n"
        "- comparing perspectives or ideologies\n"
        "- inferring motives, bias, or implications\n"
    ),
    "english": (
        "Difficulty usually increases with:\n"
        "- more inference and interpretation\n"
        "- subtle use of tone, theme, or literary devices\n"
        "- ambiguous or closely related answer options\n"
    ),
    "chemistry": (
        "Difficulty usually increases with:\n"
        "- multiple-step reasoning over reactions or concepts\n"
        "- quantitative reasoning and conceptual integration\n"
    ),
    "biology": (
        "Difficulty usually increases with:\n"
        "- multi-layered mechanisms, pathways, or interactions\n"
        "- applying concepts to new or unfamiliar contexts\n"
    ),
    "generic": (
        "Difficulty usually increases with:\n"
        "- more reasoning and abstraction\n"
        "- less direct recall\n"
        "- more complex language or structure\n"
    ),
}


class DynamicRubricGenerator:
    """
    Uses Groq to read a PDF and generate a RubricSet (levels 1..5)
    tailored to that PDF and subject, with explicit skill profiles.
    """

    def __init__(self, subject: SubjectType = "generic"):
        self.subject = subject
        self.client = GroqRubricClient()

    def _build_system_prompt(self) -> str:
        subject_hint = STATIC_SUBJECT_HINTS.get(
            self.subject, STATIC_SUBJECT_HINTS["generic"]
        )
        return (
            "You are an expert teacher and assessment designer.\n"
            "Your task is to define a RELATIVE difficulty rubric with 5 levels "
            "(1 = easiest, 5 = hardest)\n"
            "for questions generated ONLY from the given PDF content.\n\n"
            "Constraints:\n"
            "- Difficulty levels are RELATIVE within this PDF, not absolute board-exam standards.\n"
            "- Each level must specify the approximate load on four skills:\n"
            "  memory, reasoning, numerical, language. Each between 0.0 and 1.0.\n"
            "- You must return STRICT JSON matching the requested schema.\n\n"
            f"Subject-specific hints:\n{subject_hint}\n"
        )

    def _build_user_prompt(self, pdf_text: str, pdf_title: str | None = None) -> str:
        short_preview = pdf_text[:4000]  # keep prompt safe

        # NOTE: this is an f-string. All literal { and } must be doubled {{ }}.
        return f"""
Here is a preview from the PDF content (may be truncated):

{short_preview}

Your task:
Define RELATIVE difficulty levels 1..5 for MCQs generated ONLY from this PDF.
Do NOT use absolute board or IIT standards. Difficulty is local to this document.

For each level include:
- level: integer 1..5
- name: short title
- description: what makes this level hard/easy
- skill_profile: relative load from 0.0 to 1.0 across four dimensions:
    memory, reasoning, numerical, language
- example_instruction: natural language hint for generating a question at this level

Return STRICT JSON in this format:

{{
  "subject": "{self.subject}",
  "pdf_title": "{pdf_title}",
  "levels": [
    {{
      "level": 1,
      "name": "string",
      "description": "string",
      "skill_profile": {{
        "memory": 0.0,
        "reasoning": 0.0,
        "numerical": 0.0,
        "language": 0.0
      }},
      "example_instruction": "string"
    }},
    {{
      "level": 2,
      "name": "string",
      "description": "string",
      "skill_profile": {{
        "memory": 0.0,
        "reasoning": 0.0,
        "numerical": 0.0,
        "language": 0.0
      }},
      "example_instruction": "string"
    }},
    {{
      "level": 3,
      "name": "string",
      "description": "string",
      "skill_profile": {{
        "memory": 0.0,
        "reasoning": 0.0,
        "numerical": 0.0,
        "language": 0.0
      }},
      "example_instruction": "string"
    }},
    {{
      "level": 4,
      "name": "string",
      "description": "string",
      "skill_profile": {{
        "memory": 0.0,
        "reasoning": 0.0,
        "numerical": 0.0,
        "language": 0.0
      }},
      "example_instruction": "string"
    }},
    {{
      "level": 5,
      "name": "string",
      "description": "string",
      "skill_profile": {{
        "memory": 0.0,
        "reasoning": 0.0,
        "numerical": 0.0,
        "language": 0.0
      }},
      "example_instruction": "string"
    }}
  ]
}}

IMPORTANT RULES:
- The output MUST be valid JSON only.
- No explanation text outside the JSON.
"""

    def generate_from_pdf(self, pdf_path: str | Path, pdf_title: str | None = None) -> RubricSet:
        pdf_path = Path(pdf_path)
        extractor = PDFExtractor(pdf_path)
        full_text = extractor.extract_full_text()

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(full_text, pdf_title or pdf_path.name)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        raw = self.client.chat(messages)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to salvage JSON if model wraps it with extra text
            cleaned = raw[raw.find("{") : raw.rfind("}") + 1]
            data = json.loads(cleaned)

        try:
            rubric = RubricSet(**data)
        except ValidationError as e:
            raise RuntimeError(f"Rubric JSON did not match schema: {e}") from e

        return rubric
