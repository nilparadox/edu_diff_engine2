from typing import Literal, List
from pydantic import BaseModel, Field


SkillName = Literal["memory", "reasoning", "numerical", "language"]


class SkillProfile(BaseModel):
    """
    Relative load of each skill for a question at a given level.
    Values are conceptual weights between 0 and 1 (not absolute logic).
    """
    memory: float = Field(ge=0.0, le=1.0)
    reasoning: float = Field(ge=0.0, le=1.0)
    numerical: float = Field(ge=0.0, le=1.0)
    language: float = Field(ge=0.0, le=1.0)


class RubricLevel(BaseModel):
    """
    One difficulty level (e.g., 1..5) for a given PDF + subject.
    This is TEXTUAL + SKILL-BASED, not a hard numeric formula.
    """
    level: int = Field(ge=1, le=5)
    name: str
    description: str
    skill_profile: SkillProfile
    example_instruction: str = Field(
        description="Short example of how to phrase a question at this level."
    )


class RubricSet(BaseModel):
    """
    Full rubric for 1 PDF and 1 subject.
    Levels are 1..5, but their meaning is relative to THIS PDF.
    """
    subject: str
    pdf_title: str
    levels: List[RubricLevel]

    def get_level(self, level: int) -> RubricLevel:
        for rl in self.levels:
            if rl.level == level:
                return rl
        raise ValueError(f"Level {level} not found in rubric")
