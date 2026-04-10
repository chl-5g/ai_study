"""
观察者：气象站更新温度，多个展示端收到通知。

运行：python3 03_observer_weather.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, temp_c: float) -> None:
        ...


class PhoneApp(Observer):
    def update(self, temp_c: float) -> None:
        print(f"  [App] 当前气温 {temp_c:.1f}°C")


class Dashboard(Observer):
    def update(self, temp_c: float) -> None:
        f = temp_c * 9 / 5 + 32
        print(f"  [大屏] {f:.1f}°F")


class WeatherStation:
    def __init__(self) -> None:
        self._subs: list[Observer] = []
        self._temp = 0.0

    def attach(self, o: Observer) -> None:
        self._subs.append(o)

    def set_temperature(self, c: float) -> None:
        self._temp = c
        print(f"气象站: 更新为 {c}°C → 通知 {len(self._subs)} 个观察者")
        for o in self._subs:
            o.update(c)


def main() -> None:
    w = WeatherStation()
    w.attach(PhoneApp())
    w.attach(Dashboard())
    w.set_temperature(22.5)
    w.set_temperature(18.0)


if __name__ == "__main__":
    main()
