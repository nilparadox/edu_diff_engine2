from typing import Optional
from pydantic import BaseModel, Field

from .rubric_models import SkillProfile


class QuestionRequest(BaseModel):
    """
    What the user (or LogiQ) asks the engine to generate.
    """
    pdf_path: str
    subject: str = "generic"
    level: int = Field(ge=1, le=5)
    # Optional override: user can bias these skill weights
    desired_skills: Optional[SkillProfile] = None
    # Optional: text instruction like "focus on Gauss law" or "include diagrams"
    extra_instruction: Optional[str] = None


class QuestionResult(BaseModel):
    """
    What the engine returns.
    """
    question_text: str
    options: list[str]
    correct_option_index: int
    explanation: str
    level_assigned: int
    # Skill profile the engine believes this question actually uses
    effective_skills: SkillProfile
