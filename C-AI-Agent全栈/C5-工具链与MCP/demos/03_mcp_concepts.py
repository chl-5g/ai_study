#!/usr/bin/env python3
"""
C5 工具链与 MCP——MCP 协议核心概念演示

MCP（Model Context Protocol）是 Anthropic 提出的标准化协议，
让 LLM 应用能通过统一接口访问外部工具和数据源。
类比：MCP 之于 AI 工具 = USB-C 之于外设——一个标准接口连接一切。

运行方式：python3 03_mcp_concepts.py
"""

import json


# ============================================================
# 1. MCP 解决什么问题
# ============================================================
print("=" * 60)
print("1. MCP 的价值：一个标准替代 N 个定制集成")
print("=" * 60)

MCP_VALUE = """
没有 MCP 的世界（现状）：
  你的 Agent 要调 Google Drive API（OAuth2 + REST）
  又要调 GitHub API（OAuth2 + GraphQL）
  又要调自己数据库（PostgreSQL 协议）
  又要调 Slack（Webhook）
  → 每个数据源都要写专属适配器，200 个数据源 = 200 个适配器

有 MCP 的世界：
  Google Drive 实现一个 MCP Server（由 Google 维护）
  GitHub 实现一个 MCP Server（由 GitHub 维护）
  你的 Agent 只需要一个 MCP Client → 调所有 MCP Server
  → 1 个 Client + N 个标准 Server，不是 M×N 个适配器

类比的：
  MCP 之于 AI Agent = USB-C 之于外设
  USB-C 出现之前：每种外设用不同接口（串口、并口、PS/2...）
  USB-C 之后：一个接口连一切
"""

print(MCP_VALUE)


# ============================================================
# 2. MCP 协议的核心概念
# ============================================================
print("=" * 60)
print("2. MCP 协议的核心：三个角色、三个原语")
print("=" * 60)

MCP_CORE = """
MCP 的架构：

  ┌──────────┐          ┌─────────────┐          ┌──────────┐
  │  MCP     │  ←────→  │  MCP        │  ←────→  │  外部    │
  │  Host    │  JSON-RPC│  Server     │  专用 API │  服务    │
  │(Claude等)│          │(工具提供方)  │          │(GitHub等)│
  └──────────┘          └─────────────┘          └──────────┘

  角色：
  - MCP Host：AI 应用（Claude Desktop、你的 Agent）
  - MCP Client：在 Host 内部，负责与 Server 通信
  - MCP Server：提供工具/资源的外部程序

  三个核心原语：
  1. Resources（资源）：
     "给我这个文件的内容"
     类似 GET 请求——读数据

  2. Tools（工具）：
     "帮我创建一个 GitHub Issue"
     类似 POST 请求——执行动作

  3. Prompts（提示模板）：
     "用这个模板生成代码审查意见"
     预定义的 prompt 模板

  通信方式：
  - stdio（标准输入/输出）：本地进程间通信
  - HTTP + SSE：远程通信（MCP Server 可以跑在另一台机器上）
"""

print(MCP_CORE)


# ============================================================
# 3. MCP 工具定义 vs OpenAI Function Calling
# ============================================================
print("=" * 60)
print("3. MCP Server 工具定义（模拟）")
print("=" * 60)


MCP_TOOLS_SCHEMA = """
MCP 工具的 JSON Schema（概念）：

{
  "tools": [
    {
      "name": "create_github_issue",
      "description": "在指定仓库创建 Issue",
      "inputSchema": {
        "type": "object",
        "properties": {
          "repo": {"type": "string", "description": "仓库名（owner/repo 格式）"},
          "title": {"type": "string", "description": "Issue 标题"},
          "body": {"type": "string", "description": "Issue 正文"},
          "labels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "标签列表"
          }
        },
        "required": ["repo", "title"]
      }
    },
    {
      "name": "search_code",
      "description": "在代码库中搜索",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "搜索关键词"},
          "language": {"type": "string", "description": "编程语言过滤"}
        },
        "required": ["query"]
      }
    }
  ]
}
"""

print(MCP_TOOLS_SCHEMA)


# ============================================================
# 4. 用策略模式实现 MCP 工具注册
# ============================================================
print("=" * 60)
print("4. 用策略模式管理多个 MCP Server 的工具")
print("=" * 60)

from abc import ABC, abstractmethod


class MCPServer(ABC):
    """模拟一个 MCP Server 的接口"""
    @abstractmethod
    def server_name(self) -> str: ...
    @abstractmethod
    def list_tools(self) -> list[dict]: ...
    @abstractmethod
    def call_tool(self, tool_name: str, params: dict) -> str: ...


class GitHubMCPServer(MCPServer):
    """GitHub MCP Server（模拟）"""
    def server_name(self) -> str:
        return "github"

    def list_tools(self) -> list[dict]:
        return [
            {"name": "create_issue", "server": "github"},
            {"name": "search_code", "server": "github"},
            {"name": "list_repos", "server": "github"},
        ]

    def call_tool(self, tool_name: str, params: dict) -> str:
        tools = {
            "create_issue": f"创建 Issue：{params.get('title', '')}",
            "search_code": f"搜索代码：{params.get('query', '')}",
            "list_repos": "列出仓库：repo1, repo2, repo3",
        }
        return tools.get(tool_name, f"未知工具: {tool_name}")


class FilesystemMCPServer(MCPServer):
    """文件系统 MCP Server（模拟）"""
    def server_name(self) -> str:
        return "filesystem"

    def list_tools(self) -> list[dict]:
        return [
            {"name": "read_file", "server": "filesystem"},
            {"name": "write_file", "server": "filesystem"},
            {"name": "list_directory", "server": "filesystem"},
        ]

    def call_tool(self, tool_name: str, params: dict) -> str:
        path = params.get("path", "/")
        tools = {
            "read_file": f"读取文件：{path} 的内容...",
            "write_file": f"写入文件：{path}",
            "list_directory": f"列出目录：{path} → [file1.py, file2.py]",
        }
        return tools.get(tool_name, f"未知工具: {tool_name}")


class AgentToolRegistry:
    """
    Agent 的工具注册表——聚合所有 MCP Server 的工具。

    关键设计：
    - 工具名可能冲突 → 用 server_name.tool_name 作为完整标识
    - 每个 Server 独立实现，Agent 不关心内部细节（又是策略模式！）
    """

    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.all_tools: list[dict] = []

    def register_server(self, server: MCPServer):
        """注册一个 MCP Server"""
        self.servers[server.server_name()] = server
        # 把该 Server 的工具加入总列表
        for tool in server.list_tools():
            full_name = f"{server.server_name()}.{tool['name']}"
            self.all_tools.append({
                "full_name": full_name,
                "server": server.server_name(),
                "tool": tool["name"],
            })
        print(f"  📦 注册 MCP Server: {server.server_name()} "
              f"({len(server.list_tools())} 个工具)")

    def execute(self, full_tool_name: str, params: dict) -> str:
        """执行工具——通过 server.tool_name 定位"""
        if "." not in full_tool_name:
            return f"错误：工具名需包含 server 前缀，如 github.create_issue"
        server_name, tool_name = full_tool_name.split(".", 1)
        server = self.servers.get(server_name)
        if not server:
            return f"错误：未找到 MCP Server '{server_name}'"
        return server.call_tool(tool_name, params)

    def get_all_tool_schemas_for_llm(self) -> list[dict]:
        """生成给 LLM 看的完整工具列表"""
        return [
            {"name": t["full_name"], "server": t["server"]}
            for t in self.all_tools
        ]


# 使用
registry = AgentToolRegistry()
registry.register_server(GitHubMCPServer())
registry.register_server(FilesystemMCPServer())

print(f"\n  注册的工具总数: {len(registry.all_tools)}")
print("  工具列表:")
for t in registry.get_all_tool_schemas_for_llm():
    print(f"    - {t['name']}")

print("\n  模拟 LLM 调用工具：")
print(f"    {registry.execute('github.create_issue', {'title': 'Bug: 登录页报错'})}")
print(f"    {registry.execute('filesystem.read_file', {'path': '/app/main.py'})}")

print("\n✅ C5 MCP 协议概念演示完成")
