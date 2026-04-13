#!/usr/bin/env python3
"""
用 Python 调 Git：subprocess 跑下列速查命令（与 A1 §12 对照；写法统一为 git([...], cwd=repo)）。

    # 初始化 / 克隆
    git init
    git clone <url>

    # 日常
    git status                  # 看状态
    git add file.py             # 单文件暂存
    git add .                   # 所有修改暂存
    git commit -m "message"     # 提交
    git push                    # 推到远程
    git pull                    # 拉最新

    # 查看
    git log --oneline           # 简洁日志
    git log --graph --oneline --all   # 图形化
    git diff                    # 未暂存的 diff
    git diff --staged           # 已暂存的 diff
    git show <commit>           # 看某次提交的详情

    # 分支
    git branch                  # 列出分支
    git branch feat-x           # 创建分支
    git switch feat-x           # 切换（新命令，推荐）
    git checkout feat-x         # 切换（老命令，仍然支持）
    git switch -c feat-x        # 创建并切换
    git merge feat-x            # 合并
    git branch -d feat-x        # 删除

    # 撤销
    git restore file.py         # 丢弃工作区改动（新命令）
    git restore --staged file.py  # 取消暂存
    git revert <commit>         # 创建反向提交撤销某次 commit
    git reset --hard HEAD       # 把工作区重置到 HEAD（危险！会丢失改动）

    # 功能分支 + PR（另见 demo_github_pr_workflow）
    # switch main → pull → switch -c feat/... → add/commit → push -u → PR → switch main → pull → branch -d

依赖：本机 git 在 PATH；仅用标准库。

安全约定：
- 在 tempfile 里演示，结束删除目录。
- clone / push / pull 不连真实远端，只打印等价命令行（可自行改成 subprocess 真跑）。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def git(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """在 cwd 下执行 git <args>。"""
    cmd = ["git", *args]
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def print_out(cp: subprocess.CompletedProcess[str]) -> None:
    if cp.stdout:
        print(cp.stdout.rstrip())
    if cp.stderr:
        print(cp.stderr.rstrip(), file=sys.stderr)


def print_pull_only() -> None:
    print("\n$ git pull")
    print("  # 需已配置 origin；无远端时仅作流程示意，不执行 subprocess。")


def print_push_upstream(branch: str) -> None:
    print(f"\n$ git push -u origin {branch}")
    print("  # 需已 git remote add origin <url>；此处仅打印，避免误推。")


def demo_github_pr_workflow() -> None:
    """
    典型「从 main 开分支 → 小步提交 → 推远端提 PR → 合并后本地清理」流程。

    无配置 remote 时：pull / push 只打印；用本地 merge 模拟「PR 已合入 main」。
    """
    tmp = Path(tempfile.mkdtemp(prefix="git_pr_flow_"))
    feat = "feat/user-auth"
    print(f"\n{'=' * 60}\n# 功能分支 + PR 工作流（临时仓库: {tmp}）\n{'=' * 60}")

    try:
        git(["init"], cwd=tmp)
        git(["config", "user.email", "demo@example.local"], cwd=tmp)
        git(["config", "user.name", "Demo User"], cwd=tmp)
        (tmp / "README.md").write_text("# app\n", encoding="utf-8")
        git(["add", "README.md"], cwd=tmp)
        git(["commit", "-m", "chore: init repo"], cwd=tmp)
        git(["branch", "-M", "main"], cwd=tmp)  # 确保主分支名为 main

        # 1. 开新功能前，从 main 拉最新
        print("\n# --- 1. 开新功能前，从 main 拉最新 ---")
        cp = git(["switch", "main"], cwd=tmp)
        print_out(cp)
        print_pull_only()

        # 2. 创建功能分支
        print("\n# --- 2. 创建功能分支 ---")
        git(["switch", "-c", feat], cwd=tmp)

        # 3. 开发 + 多次提交（小而频繁）
        print("\n# --- 3. 开发 + 多次提交 ---")
        (tmp / "templates").mkdir(parents=True, exist_ok=True)
        (tmp / "templates" / "login.html").write_text(
            "<html><!-- login skeleton --></html>\n",
            encoding="utf-8",
        )
        git(["add", "."], cwd=tmp)
        git(["commit", "-m", "feat: 添加登录页面骨架"], cwd=tmp)

        (tmp / "auth.py").write_text("# JWT verify placeholder\n", encoding="utf-8")
        git(["add", "."], cwd=tmp)
        git(["commit", "-m", "feat: 添加 JWT 验证"], cwd=tmp)
        print_out(git(["log", "--oneline", "-n", "5"], cwd=tmp))

        # 4. 推送分支
        print("\n# --- 4. 推送分支 ---")
        print_push_upstream(feat)

        # 5. 在 GitHub 提 PR（仅说明）
        print("\n# --- 5. 在 GitHub 提 PR ---")
        print("  # 浏览器打开仓库 → Compare & pull request → 评审后 Merge 到 main")

        # 6. 本地清理：switch main → pull → branch -d（无 origin 时 pull 仅打印；merge 模拟 PR 合入后 pull 得到的 main）
        print("\n# --- 6. 本地清理 ---")
        git(["switch", "main"], cwd=tmp)
        print_pull_only()
        git(["merge", feat, "-m", f"Merge branch '{feat}'"], cwd=tmp)
        print(
            "  # 真仓库：PR 在 GitHub 合并后，上一步 pull 会把合并结果拉到 main，通常无需再本地 merge。",
        )
        git(["branch", "-d", feat], cwd=tmp)
        print_out(git(["branch", "-a"], cwd=tmp))
        print_out(git(["log", "--oneline", "--graph", "-n", "6"], cwd=tmp))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"\n已删除临时目录: {tmp}")


def print_remote_cheatsheet(default_branch: str) -> None:
    """clone / push / pull：只打印，避免误连远端。"""
    print("\n# ---------- 初始化 / 克隆（真仓库里执行；此处仅打印）----------")
    for line in (
        "git clone <url>              # 已有目录则: git clone <url> mydir",
        "git init                       # 本脚本已在临时目录演示 init",
    ):
        print(f"  {line}")

    print("\n# ---------- push / pull（需先 git remote add …）----------")
    for line in (
        f"git push                       # 或: git push -u origin {default_branch}",
        "git pull                       # 或: git pull --rebase origin <branch>",
    ):
        print(f"  {line}")
    print("  # Python: subprocess.run([\"git\", \"push\"], cwd=repo_root)")


def demo_full_cheatsheet() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="git_demo_"))
    print(f"临时仓库: {tmp}")

    try:
        # ========== 初始化 ==========
        git(["init"], cwd=tmp)
        git(["config", "user.email", "demo@example.local"], cwd=tmp)
        git(["config", "user.name", "Demo User"], cwd=tmp)

        # ========== 日常：status / add 单文件 / commit ==========
        (tmp / "file.py").write_text("# v0\n", encoding="utf-8")
        cp = git(["status"], cwd=tmp)
        print_out(cp)

        git(["add", "file.py"], cwd=tmp)  # git add file.py
        cp = git(["status", "-sb"], cwd=tmp)
        print_out(cp)
        git(["commit", "-m", "init: file.py"], cwd=tmp)
        print_out(git(["log", "-1", "--oneline"], cwd=tmp))

        # git add .
        (tmp / "other.py").write_text("# other\n", encoding="utf-8")
        (tmp / "readme.txt").write_text("doc\n", encoding="utf-8")
        cp = git(["status", "-sb"], cwd=tmp)
        print_out(cp)
        git(["add", "."], cwd=tmp)  # git add .
        git(["commit", "-m", "chore: add other.py and readme"], cwd=tmp)

        default_branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=tmp).stdout.strip()

        # ========== 查看：log / diff / show ==========
        (tmp / "file.py").write_text("# v1 unstaged\n", encoding="utf-8")
        cp = git(["diff"], cwd=tmp)  # 未暂存
        print_out(cp)
        git(["add", "file.py"], cwd=tmp)
        cp = git(["diff", "--staged"], cwd=tmp)  # 已暂存
        print_out(cp)
        git(["commit", "-m", "feat: bump file.py"], cwd=tmp)

        cp = git(["log", "--oneline"], cwd=tmp)
        print_out(cp)
        cp = git(["log", "--graph", "--oneline", "--all"], cwd=tmp)
        print_out(cp)

        mid = git(["rev-parse", "HEAD~1"], cwd=tmp).stdout.strip()
        cp = git(["show", mid, "--stat"], cwd=tmp)  # git show <commit>
        print_out(cp)

        # ========== 分支：branch / switch -c / switch / checkout / merge / -d ==========
        cp = git(["branch"], cwd=tmp)
        print_out(cp)

        git(["branch", "feat-x"], cwd=tmp)  # git branch feat-x（不切换）
        cp = git(["branch"], cwd=tmp)
        print_out(cp)

        git(["switch", "feat-x"], cwd=tmp)  # git switch feat-x
        (tmp / "feat.txt").write_text("feat\n", encoding="utf-8")
        git(["add", "feat.txt"], cwd=tmp)
        git(["commit", "-m", "feat: feat.txt"], cwd=tmp)

        git(["checkout", default_branch], cwd=tmp)  # git checkout <branch>（老写法）
        git(["merge", "feat-x", "-m", "merge: integrate feat-x"], cwd=tmp)  # git merge feat-x
        git(["branch", "-d", "feat-x"], cwd=tmp)  # git branch -d feat-x（已合并）

        cp = git(["log", "--graph", "--oneline", "--all", "-n", "8"], cwd=tmp)
        print_out(cp)

        # switch -c：从当前 HEAD 新建并切换
        git(["switch", "-c", "short-lived"], cwd=tmp)
        git(["commit", "--allow-empty", "-m", "chore: empty on short-lived"], cwd=tmp)
        git(["switch", default_branch], cwd=tmp)
        git(["merge", "short-lived", "-m", "merge short-lived"], cwd=tmp)
        git(["branch", "-d", "short-lived"], cwd=tmp)  # git branch -d（已合并可删）

        cp = git(["branch"], cwd=tmp)
        print_out(cp)

        # ========== 撤销：restore / restore --staged / revert ==========
        (tmp / "file.py").write_text("# dirty working tree\n", encoding="utf-8")
        cp = git(["status", "-sb"], cwd=tmp)
        print_out(cp)
        git(["restore", "file.py"], cwd=tmp)  # git restore file.py
        print_out(git(["status", "-sb"], cwd=tmp))

        (tmp / "file.py").write_text("# staged only\n", encoding="utf-8")
        git(["add", "file.py"], cwd=tmp)
        git(["restore", "--staged", "file.py"], cwd=tmp)  # 取消暂存
        print_out(git(["status", "-sb"], cwd=tmp))
        git(["restore", "file.py"], cwd=tmp)  # 再丢工作区
        print_out(git(["status", "-sb"], cwd=tmp))

        # revert：造一个可撤销提交
        (tmp / "bad.txt").write_text("oops\n", encoding="utf-8")
        git(["add", "bad.txt"], cwd=tmp)
        bad_commit = git(["commit", "-m", "chore: add bad.txt"], cwd=tmp)
        print_out(bad_commit)
        bad_sha = git(["rev-parse", "HEAD"], cwd=tmp).stdout.strip()
        cp = git(["revert", "--no-edit", bad_sha], cwd=tmp)  # git revert <commit>
        print_out(cp)

        # ========== reset --hard（危险：演示末尾、马上删库）==========
        (tmp / "wipe_me.txt").write_text("will disappear\n", encoding="utf-8")
        print_out(git(["status", "-sb"], cwd=tmp))
        cp = git(["reset", "--hard", "HEAD"], cwd=tmp)  # git reset --hard HEAD
        print_out(cp)
        # 注：未跟踪文件（如 wipe_me.txt）默认不会被 reset --hard 删除；仅把已跟踪文件对齐到 HEAD。
        # 再演示：已跟踪文件的工作区改动被硬重置掉。
        (tmp / "file.py").write_text("# gone after hard\n", encoding="utf-8")
        git(["add", "file.py"], cwd=tmp)
        git(["commit", "-m", "chore: for hard reset demo"], cwd=tmp)
        (tmp / "file.py").write_text("# dirty again\n", encoding="utf-8")
        git(["reset", "--hard", "HEAD"], cwd=tmp)
        print_out(git(["status", "-sb"], cwd=tmp))

        print_remote_cheatsheet(default_branch)

        print("\n# ---------- 其它常用（自行改成 git([...], cwd=...)）----------")
        extras = (
            "git fetch origin",
            "git remote -v",
            "git stash push -m WIP",
            "git cherry-pick <sha>",
        )
        for x in extras:
            print(f"  {x}")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"\n已删除临时目录: {tmp}")


def main() -> None:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("未找到 git，请先安装 Git 并加入 PATH。", file=sys.stderr)
        sys.exit(1)

    demo_full_cheatsheet()
    demo_github_pr_workflow()


if __name__ == "__main__":
    main()
