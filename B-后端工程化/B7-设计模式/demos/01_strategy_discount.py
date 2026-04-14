"""
策略模式：按「促销规则」计算价格，避免 endless if-else。

运行：python3 01_strategy_discount.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class PricingStrategy(ABC):
    @abstractmethod
    def line_total(self, unit_price: float, qty: int) -> float:
        ...


class RegularPrice(PricingStrategy):
    def line_total(self, unit_price: float, qty: int) -> float:
        return unit_price * qty


class VipDiscount(PricingStrategy):
    def __init__(self, ratio: float = 0.85) -> None:
        self.ratio = ratio

    def line_total(self, unit_price: float, qty: int) -> float:
        return unit_price * qty * self.ratio


class FlashSale(PricingStrategy):
    def line_total(self, unit_price: float, qty: int) -> float:
        return min(unit_price * qty, 99.0)


@dataclass
class CartLine:
    unit_price: float
    qty: int
    strategy: PricingStrategy

    def total(self) -> float:
        return self.strategy.line_total(self.unit_price, self.qty)


def main() -> None:
    lines = [
        CartLine(100, 1, RegularPrice()),
        CartLine(100, 1, VipDiscount()),
        CartLine(200, 1, FlashSale()),
    ]
    for i, ln in enumerate(lines):
        print(f"line {i}: {ln.total():.2f}")


if __name__ == "__main__":
    main()
