import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env in project root


def get_groq_internal_key() -> str:
    """
    Returns the internal Groq API key used for rubric generation.
    """
    key = os.getenv("GROQ_INTERNAL_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_INTERNAL_API_KEY is missing. "
            "Set it in your .env file at project root."
        )
    return key
