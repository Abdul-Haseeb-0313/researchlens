import re


def clean_text(text: str) -> str:
    """
    Clean text extracted from a PDF.

    The goal is to remove common PDF extraction artifacts
    while preserving the original meaning and structure.
    """

    if not text:
        return ""

    # Normalize different newline characters
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove trailing whitespace from each line
    text = "\n".join(line.strip() for line in text.splitlines())

    # Fix words broken across lines by a hyphen.
    # Example:
    # "transfor-\nmer" -> "transformer"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Replace single newlines inside sentences with spaces.
    # Keep paragraph breaks (two or more newlines).
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Normalize excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()