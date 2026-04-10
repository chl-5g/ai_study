# B9 设计模式 — `demos/` 说明

GoF 中三类各给**一个最小可运行**示例（无第三方依赖），便于改坏再修。

```bash
cd demos
python3 01_strategy_discount.py
python3 02_chain_approval.py
python3 03_observer_weather.py
```

| 文件 | GoF 类型 | 要点 |
|------|----------|------|
| `01_strategy_discount.py` | 行为型 · 策略 | 替换算法族，干掉 long if-else |
| `02_chain_approval.py` | 行为型 · 责任链 | 多个 handler 依次尝试 |
| `03_observer_weather.py` | 行为型 · 观察者 | 主题变更通知订阅者 |

更多模式请对照 [`../理论讲解.md`](../理论讲解.md)（GoF 见该文 **§2 整合速览**）。
