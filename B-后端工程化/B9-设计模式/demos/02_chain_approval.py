"""
责任链：请假天数逐级审批，链上每一环决定是否处理或交给下一环。

运行：python3 02_chain_approval.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Request:
    employee: str
    days: float


class Handler(ABC):
    def __init__(self) -> None:
        self._next: Handler | None = None

    def set_next(self, h: Handler) -> Handler:
        self._next = h
        return h

    def handle(self, req: Request) -> str:
        result = self._try_handle(req)
        if result is not None:
            return result
        if self._next is None:
            return "无人处理"
        return self._next.handle(req)

    @abstractmethod
    def _try_handle(self, req: Request) -> str | None:
        ...


class TeamLead(Handler):
    def _try_handle(self, req: Request) -> str | None:
        if req.days <= 1:
            return f"{req.employee}: 组长已批 {req.days} 天"
        return None


class Manager(Handler):
    def _try_handle(self, req: Request) -> str | None:
        if req.days <= 3:
            return f"{req.employee}: 经理已批 {req.days} 天"
        return None


class Director(Handler):
    def _try_handle(self, req: Request) -> str | None:
        return f"{req.employee}: 总监已批 {req.days} 天"


def main() -> None:
    chain = TeamLead()
    chain.set_next(Manager()).set_next(Director())

    for days in (0.5, 2, 5):
        print(chain.handle(Request("Alice", days)))


if __name__ == "__main__":
    main()
