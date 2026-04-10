# C5 工具链与 MCP — `demos/` 说明

与 [`../理论讲解.md`](../理论讲解.md) 配套：在正式 MCP SDK 之前，用**最小注册表**与 **stdio JSON 行协议**理解「工具发现 + 远程调用」的形状。

```bash
cd demos
python3 01_tool_registry.py

# 默认：一次性打印 list/call 演示
python3 02_stdio_tool_host.py

# 交互：另一终端运行后，stdin 每行一个 JSON
python3 02_stdio_tool_host.py --server
# 示例行：{"cmd":"list_tools"}
#         {"cmd":"call","name":"echo","arguments":{"text":"hi"}}
```

| 文件 | 要点 | 依赖 |
|------|------|------|
| `01_tool_registry.py` | `ToolRegistry`：注册可调用、`list_openai_tools()`、`call()` | 无 |
| `02_stdio_tool_host.py` | 极简宿主：`list_tools` / `call`；`--server` 读 stdin | 无 |

生产环境接入 MCP 请使用官方 `mcp` SDK（版本以文档为准）；本目录 demo 刻意保持零第三方，便于对照协议心智模型。
