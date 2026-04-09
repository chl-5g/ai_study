#!/usr/bin/env python3
"""
综合项目：命令行 Todo 应用
综合运用 OOP + 文件存储 + json + datetime + 类型提示

功能：添加任务、列出任务、完成任务、删除任务、持久化存储
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional


class Todo:
    """单个待办事项"""

    def __init__(self, title: str, done: bool = False, created_at: str = None):
        self.title = title
        self.done = done
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> dict:
        """转为字典（用于 JSON 序列化）"""
        return {
            "title": self.title,
            "done": self.done,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Todo":
        """从字典创建（用于 JSON 反序列化）"""
        return cls(
            title=data["title"],
            done=data["done"],
            created_at=data.get("created_at"),
        )

    def __str__(self) -> str:
        status = "[x]" if self.done else "[ ]"
        return f"{status} {self.title} ({self.created_at})"


class TodoApp:
    """
    Todo 应用主类
    演示：封装、文件操作、JSON 持久化
    """

    def __init__(self, filepath: str = None):
        # 默认存储在脚本同目录下
        if filepath is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(script_dir, "_todo_data.json")
        self.filepath = filepath
        self.todos: list[Todo] = []
        self._load()  # 启动时加载数据

    def _load(self) -> None:
        """从 JSON 文件加载数据"""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.todos = [Todo.from_dict(item) for item in data]

    def _save(self) -> None:
        """保存数据到 JSON 文件"""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(
                [todo.to_dict() for todo in self.todos],
                f, ensure_ascii=False, indent=2
            )

    def add(self, title: str) -> None:
        """添加新任务"""
        todo = Todo(title)
        self.todos.append(todo)
        self._save()
        print(f"  + 已添加: {todo}")

    def list_all(self) -> None:
        """列出所有任务"""
        if not self.todos:
            print("  (空空如也，添加一些任务吧！)")
            return

        # 未完成在前，已完成在后
        undone = [(i, t) for i, t in enumerate(self.todos, 1) if not t.done]
        done = [(i, t) for i, t in enumerate(self.todos, 1) if t.done]

        if undone:
            print("  --- 待完成 ---")
            for idx, todo in undone:
                print(f"  {idx}. {todo}")
        if done:
            print("  --- 已完成 ---")
            for idx, todo in done:
                print(f"  {idx}. {todo}")
        print(f"\n  总计: {len(self.todos)} 项 (未完成: {len(undone)}, 已完成: {len(done)})")

    def complete(self, index: int) -> None:
        """标记任务为完成"""
        if 1 <= index <= len(self.todos):
            self.todos[index - 1].done = True
            self._save()
            print(f"  v 已完成: {self.todos[index - 1].title}")
        else:
            print(f"  ! 无效编号: {index}")

    def delete(self, index: int) -> None:
        """删除任务"""
        if 1 <= index <= len(self.todos):
            removed = self.todos.pop(index - 1)
            self._save()
            print(f"  - 已删除: {removed.title}")
        else:
            print(f"  ! 无效编号: {index}")

    def clear_done(self) -> None:
        """清除所有已完成的任务"""
        before = len(self.todos)
        self.todos = [t for t in self.todos if not t.done]
        after = len(self.todos)
        self._save()
        print(f"  清除了 {before - after} 个已完成任务")


def print_help():
    """打印帮助信息"""
    print("""
  Todo CLI 使用方法:
    add <标题>      添加新任务
    list            列出所有任务
    done <编号>     标记任务为完成
    del <编号>      删除任务
    clear           清除已完成任务
    help            显示帮助
    quit            退出
    """)


def interactive_mode(app: TodoApp):
    """交互式模式"""
    print("\n  === Todo CLI ===")
    print("  输入 'help' 查看命令\n")
    app.list_all()

    while True:
        try:
            cmd = input("\n  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  再见！")
            break

        if not cmd:
            continue

        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if action == "add" and arg:
            app.add(arg)
        elif action == "list" or action == "ls":
            app.list_all()
        elif action == "done" and arg.isdigit():
            app.complete(int(arg))
        elif action == "del" and arg.isdigit():
            app.delete(int(arg))
        elif action == "clear":
            app.clear_done()
        elif action in ("quit", "exit", "q"):
            print("  再见！")
            break
        elif action == "help":
            print_help()
        else:
            print(f"  ? 未知命令: {cmd}（输入 help 查看帮助）")


if __name__ == "__main__":
    app = TodoApp()

    # 如果有命令行参数，执行单条命令；否则进入交互模式
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        arg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

        if action == "add" and arg:
            app.add(arg)
        elif action == "list":
            app.list_all()
        elif action == "done" and arg.isdigit():
            app.complete(int(arg))
        elif action == "del" and arg.isdigit():
            app.delete(int(arg))
        else:
            print_help()
    else:
        # 演示模式：展示基本功能
        print("=" * 60)
        print("Todo CLI 演示")
        print("=" * 60)

        # 清空旧数据
        app.todos = []
        app._save()

        # 添加任务
        app.add("学习 Python OOP")
        app.add("完成 Type Hints Demo")
        app.add("复习 collections 模块")

        print()
        app.list_all()

        # 完成一个任务
        print()
        app.complete(1)

        print()
        app.list_all()

        # 清理演示数据
        os.remove(app.filepath) if os.path.exists(app.filepath) else None
        print(f"\n  (演示数据已清理)")
        print(f"  交互模式: python3 {os.path.basename(__file__)}")
        print(f"  命令模式: python3 {os.path.basename(__file__)} add '学习Python'")
