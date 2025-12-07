from pathlib import Path
from typing import Optional, Dict, Any, List

from rich import print

from .dynamic_rubric_generator import DynamicRubricGenerator, SubjectType
from .rubric_models import RubricSet, SkillProfile
from .question_models import QuestionRequest, QuestionResult
from ..utils.pdf_loader import PDFExtractor
from ..api.base_question_api import BaseQuestionAPI


class DifficultyEngine:
    """
    Main orchestrator:
    - builds or reuses a rubric for a PDF
    - combines rubric level + skill profile + PDF context
    - calls user-provided external API to generate MCQs
    """

    def __init__(self, external_api: BaseQuestionAPI):
        self.external_api = external_api
        # Simple in-memory cache: { (pdf_path, subject): RubricSet }
        self._rubric_cache: Dict[tuple[str, str], RubricSet] = {}

    def _get_or_build_rubric(self, pdf_path: Path, subject: SubjectType) -> RubricSet:
        key = (str(pdf_path), subject)
        if key in self._rubric_cache:
            return self._rubric_cache[key]

        print(f"[cyan]Building dynamic rubric for {pdf_path} (subject={subject})[/cyan]")
        gen = DynamicRubricGenerator(subject=subject)
        rubric = gen.generate_from_pdf(pdf_path)
        self._rubric_cache[key] = rubric
        return rubric

    def _build_prompt(
        self,
        pdf_text: str,
        rubric_level,
        request: QuestionRequest,
    ) -> list[dict[str, Any]]:
        """
        Build messages for the external question API.
        We will ask it to return a JSON MCQ.
        """

        # Merge rubric skill profile with optional user overrides
        base_sp: SkillProfile = rubric_level.skill_profile
        if request.desired_skills:
            sp = SkillProfile(
                memory=request.desired_skills.memory or base_sp.memory,
                reasoning=request.desired_skills.reasoning or base_sp.reasoning,
                numerical=request.desired_skills.numerical or base_sp.numerical,
                language=request.desired_skills.language or base_sp.language,
            )
        else:
            sp = base_sp

        system_msg = (
            "You are an expert question-setter for competitive exams.\n"
            "You must generate a single high-quality MCQ based ONLY on the given PDF content.\n"
            "Difficulty is RELATIVE to this PDF, not absolute.\n"
            "You will be given a rubric level and skill profile for this question.\n"
            "You MUST return STRICT JSON with keys:\n"
            "  question_text: string\n"
            "  options: list of 4 strings\n"
            "  correct_option_index: integer 0..3\n"
            "  explanation: string\n"
        )

        user_msg = f"""
PDF CONTENT (TRUNCATED):
------------------------
{pdf_text[:6000]}

RUBRIC LEVEL:
-------------
Level: {rubric_level.level} - {rubric_level.name}
Description: {rubric_level.description}
Example instruction: {rubric_level.example_instruction}

DESIRED SKILL PROFILE (0.0 to 1.0):
-----------------------------------
memory:   {sp.memory}
reasoning:{sp.reasoning}
numerical:{sp.numerical}
language: {sp.language}

EXTRA INSTRUCTION FROM USER (optional):
---------------------------------------
{request.extra_instruction or ""}

TASK:
-----
1. Create ONE MCQ that:
   - depends only on the above PDF content.
   - matches the difficulty description for this level.
   - roughly matches the skill profile emphasis.
2. The question should be clearly answerable from the PDF context,
   but not trivial (unless level=1).
3. Return ONLY valid JSON with fields:
   "question_text", "options", "correct_option_index", "explanation".
"""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

    def generate_question(self, request: QuestionRequest) -> QuestionResult:
        pdf_path = Path(request.pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        subject: SubjectType = request.subject.lower() if request.subject else "generic"  # type: ignore

        rubric = self._get_or_build_rubric(pdf_path, subject)

        try:
            lvl = rubric.get_level(request.level)
        except ValueError:
            raise ValueError(f"Requested level {request.level} not defined in rubric.")

        extractor = PDFExtractor(pdf_path)
        pdf_text = extractor.extract_full_text()

        messages = self._build_prompt(pdf_text, lvl, request)

        raw = self.external_api.generate(messages)

        import json
        data = json.loads(raw)

        sp = request.desired_skills or lvl.skill_profile

        return QuestionResult(
            question_text=data["question_text"],
            options=data["options"],
            correct_option_index=data["correct_option_index"],
            explanation=data["explanation"],
            level_assigned=lvl.level,
            effective_skills=sp,
        )

    def generate_questions(
        self,
        request: QuestionRequest,
        count: int = 10,
        max_attempts_factor: int = 3,
    ) -> list[QuestionResult]:
        """
        Generate up to `count` non-duplicate questions for the same request.

        Parameters
        ----------
        request : QuestionRequest
            The single-question request (pdf_path, subject, level, etc.).
        count : int
            How many questions to try to generate.
        max_attempts_factor : int
            Safety multiplier to avoid infinite loops. Maximum attempts
            will be count * max_attempts_factor.

        Returns
        -------
        list[QuestionResult]
            A list of QuestionResult objects with unique question_text.
        """
        results: List[QuestionResult] = []
        seen_texts = set()

        max_attempts = count * max_attempts_factor
        attempts = 0

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            try:
                res = self.generate_question(request)
            except Exception:
                # If one generation fails, skip and try again
                continue

            qtext = (res.question_text or "").strip()
            if not qtext:
                continue
            if qtext in seen_texts:
                # duplicate question, skip
                continue

            seen_texts.add(qtext)
            results.append(res)

        return results
