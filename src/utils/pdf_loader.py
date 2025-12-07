from pathlib import Path
from typing import List
import pdfplumber


class PDFExtractor:
    """
    Helper to extract text from a PDF.
    Later we can add smarter chunking by headings / sections etc.
    """

    def __init__(self, path: str | Path, max_pages: int | None = None):
        self.path = Path(path)
        self.max_pages = max_pages

    def extract_pages(self) -> List[str]:
        if not self.path.exists():
            raise FileNotFoundError(f"PDF not found: {self.path}")

        texts: List[str] = []
        with pdfplumber.open(self.path) as pdf:
            for i, page in enumerate(pdf.pages):
                if self.max_pages is not None and i >= self.max_pages:
                    break
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    texts.append(text)
        return texts

    def extract_full_text(self) -> str:
        """
        Returns all pages joined as one big string.
        """
        return "\n\n".join(self.extract_pages())
