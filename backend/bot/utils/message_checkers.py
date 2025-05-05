from typing import Union

import emoji


def emoji_check(text: str) -> Union[str, bool]:
    return text if emoji.is_emoji(text) else False
