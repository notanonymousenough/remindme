import re

GLOBAL_ESCAPE_CHARS = r'_*[]()~`>#+=\|{}.!-'
GLOBAL_ESCAPE_PATTERN = re.compile(f'([{re.escape(GLOBAL_ESCAPE_CHARS)}])')

# Внутри [текст ссылки] экранируются только ] и \
TEXT_ESCAPE_CHARS = ']]\\\\' # Правильное представление строки ']\'
TEXT_ESCAPE_PATTERN = re.compile(f'([{re.escape(TEXT_ESCAPE_CHARS)}])')

# Внутри (url ссылки) экранируются только ) и \
URL_ESCAPE_CHARS = ')]\\\\' # Правильное представление строки ')\'
URL_ESCAPE_PATTERN = re.compile(f'([{re.escape(URL_ESCAPE_CHARS)}])')

# Паттерн для поиска ссылок [текст](url)
LINK_PATTERN = re.compile(r'[(.*?)]((.*?))')

def parse_for_markdown(text: str) -> str:
    """
    Экранирует текст для MarkdownV2, учитывая ссылки формата [текст](url).
    Внутри [] и () экранируются только разрешенные символы.
    Вне ссылок экранируются все необходимые символы.
    """
    result = []
    last_pos = 0

    # Ищем все ссылки в тексте
    for match in LINK_PATTERN.finditer(text):
        link_start, link_end = match.span()
        link_text_content = match.group(1)
        link_url_content = match.group(2)

        # Экранируем текст перед ссылкой (полным набором символов)
        before_link_text = text[last_pos:link_start]
        result.append(GLOBAL_ESCAPE_PATTERN.sub(r'\\\1', before_link_text))

        # Экранируем текст внутри [] (только ] и )
        escaped_text_content = TEXT_ESCAPE_PATTERN.sub(r'\\\1', link_text_content)
        # Экранируем текст внутри () (только ) и )
        escaped_url_content = URL_ESCAPE_PATTERN.sub(r'\\\1', link_url_content)

        # Собираем ссылку обратно, уже с экранированными частями
        # Сами скобки []() и их содержимое не попадают под глобальное экранирование благодаря логике
        result.append(f'[{escaped_text_content}]({escaped_url_content})')

        # Обновляем позицию, с которой продолжим поиск
        last_pos = link_end

    # Экранируем оставшийся текст после последней ссылки (полным набором символов)
    remaining_text = text[last_pos:]
    result.append(GLOBAL_ESCAPE_PATTERN.sub(r'\\\1', remaining_text))

    return "".join(result)

def OLD_parse_for_markdown(text: str) -> str:
    """Экранирует специальные символы Markdown в строке."""
    special_chars = r'([][_*()~`>#+=\|{}.!-])'
    return re.sub(special_chars, r'\\\1', text)
