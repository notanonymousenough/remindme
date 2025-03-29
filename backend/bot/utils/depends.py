from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Any, Coroutine


@dataclass(frozen=True, slots=True)
class Depends:
    """
    По сути, предоставляет кэшированный результат выполнения функции, если `use_cache=True`.
    Функция обычно выполняется только один раз для каждой области видимости (например, запроса)
    при первом запросе зависимости, и последующие использования в той же области видимости
    будут использовать уже закешированный результат.
    """
    func: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]] | None = None
    use_cache: bool = field(default=True, kw_only=True)
