from __future__ import annotations


class ConsoleIO:
    def show(self, message: str) -> None:
        print(message)

    def prompt(self, message: str) -> str:
        return input(message)
