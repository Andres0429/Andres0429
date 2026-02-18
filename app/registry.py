from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Registry:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Callable[..., Any]]] = {
            "arv": {},
            "mao": {},
            "extractor": {},
        }

    def register(self, namespace: str, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._items.setdefault(namespace, {})[name] = func
            return func

        return decorator

    def get(self, namespace: str, name: str) -> Callable[..., Any]:
        try:
            return self._items[namespace][name]
        except KeyError as exc:
            raise ValueError(f"{namespace} strategy '{name}' not registered") from exc

    def has(self, namespace: str, name: str) -> bool:
        return name in self._items.get(namespace, {})


registry = Registry()


def register_arv(name: str):
    return registry.register("arv", name)


def register_mao(name: str):
    return registry.register("mao", name)


def register_extractor(name: str):
    return registry.register("extractor", name)
