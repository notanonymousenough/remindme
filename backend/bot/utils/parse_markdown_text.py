import re


def parse_for_markdown(text: str) -> str:
    """Экранирует специальные символы Markdown в строке."""
    special_chars = r'([-.!():])'
    return re.sub(special_chars, r'\\\1', text)
