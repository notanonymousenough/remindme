import emoji


def emoji_check(text: str):
    return emoji.is_emoji(text)
