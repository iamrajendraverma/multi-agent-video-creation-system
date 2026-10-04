from pathlib import Path
from string import Template


PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str, **variables) -> str:
    """
    Load prompts/<name>.txt and fill in its $placeholders.
    Raises KeyError if a placeholder has no value.
    """

    template = Template((PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8"))

    return template.substitute(**variables).strip()
