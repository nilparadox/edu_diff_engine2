from pathlib import Path
from rich import print

from .api.openai_question_api import OpenAIQuestionAPI
from .core.engine import DifficultyEngine
from .core.question_models import QuestionRequest


def main():
    # 1) Ask for API key (not stored anywhere)
    print("[yellow]Enter your OpenAI API key (not stored anywhere):[/yellow]")
    api_key = input().strip()
    if not api_key:
        print("[red]No API key provided. Exiting.[/red]")
        return

    # 2) Ask for PDF path
    print("[yellow]Enter path to PDF (e.g., example.pdf):[/yellow]")
    pdf_input = input().strip()
    pdf_path = Path(pdf_input)
    if not pdf_path.exists():
        print(f"[red]PDF not found: {pdf_path}[/red]")
        return

    # 3) Ask for desired difficulty level (1–5)
    print("[yellow]Enter desired difficulty level (1-5):[/yellow]")
    level_str = input().strip()
    try:
        level = int(level_str)
    except ValueError:
        print("[red]Invalid level. Must be an integer between 1 and 5.[/red]")
        return
    if level < 1 or level > 5:
        print("[red]Level must be between 1 and 5.[/red]")
        return

    # 4) Ask for subject (optional)
    print("[yellow]Enter subject (physics/math/history/english/chemistry/biology or leave blank for generic):[/yellow]")
    subject = input().strip().lower() or "generic"

    # 5) Extra instruction (optional)
    print("[yellow]Any extra instruction for question generation? (press Enter to skip)[/yellow]")
    extra_instruction = input().strip() or None

    # 6) Build external API + engine
    external_api = OpenAIQuestionAPI(api_key=api_key)
    engine = DifficultyEngine(external_api=external_api)

    # 7) Build request object
    req = QuestionRequest(
        pdf_path=str(pdf_path),
        subject=subject,
        level=level,
        desired_skills=None,  # can add sliders later
        extra_instruction=extra_instruction,
    )

    # 8) Generate question
    print("[cyan]Generating question...[/cyan]")
    result = engine.generate_question(req)

    # 9) Print result nicely
    print("\n[bold green]Question:[/bold green]")
    print(result.question_text)

    print("\n[bold]Options:[/bold]")
    for i, opt in enumerate(result.options):
        print(f"{i}. {opt}")

    print(f"\n[bold]Correct index:[/bold] {result.correct_option_index}")
    print(f"[bold]Explanation:[/bold] {result.explanation}")

    print(f"\n[bold]Level (requested):[/bold] {result.level_assigned}")
    print(f"[bold]Skills:[/bold] {result.effective_skills}")


if __name__ == "__main__":
    main()
