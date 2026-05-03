#!/usr/bin/env python3
"""
Docker 多阶段构建演示（概念代码 + 内嵌 Dockerfile 说明）

多阶段构建解决：最终镜像里只放运行时需要的东西，不包含编译工具、开发依赖
好处：镜像体积大幅缩小（从 GB 级别降到 MB 级别）

运行方式：阅读本文件的注释和伪代码即可理解概念。
实际执行需要 docker 环境，见每个示例前的说明。
"""


# ============================================================
# 示例 1：Python FastAPI 应用的多阶段构建
# ============================================================
print("=" * 60)
print("示例 1：Python 多阶段构建")
print("=" * 60)

multi_stage_dockerfile = """
# ========================================
# 阶段 1：builder（构建阶段）
# ========================================
FROM python:3.11-slim AS builder
#   ↑ AS builder 给这个阶段起个名字，后面可以 --from=builder 引用它

# 安装构建工具（只在 build 阶段需要）
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# 复制依赖清单
COPY requirements.txt .

# 安装依赖到 /install 目录（不是系统全局）
# --user 装到用户目录，--no-cache-dir 不缓存下载的包（减小体积）
RUN pip install --user --no-cache-dir -r requirements.txt

# ========================================
# 阶段 2：runtime（运行阶段）
# ========================================
FROM python:3.11-slim
#   ↑ 这是一个全新的、干净的 Python 基础镜像，没有 gcc 等构建工具

# 从 builder 阶段复制已安装的包（关键！）
COPY --from=builder /root/.local /root/.local

# 把 pip 安装的用户级可执行文件加入 PATH
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
WORKDIR /app
COPY . .

# 用非 root 用户运行（安全最佳实践）
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# 效果对比：
#  没有多阶段：镜像里有 gcc、头文件、pip 缓存 → ~1.2GB
#  多阶段构建：只有运行时依赖 → ~200MB
#  体积缩小 ~80%
"""

print(multi_stage_dockerfile)


# ============================================================
# 示例 2：前端 Node.js 构建 + 后端 Python 的混合多阶段
# ============================================================
print("\n" + "=" * 60)
print("示例 2：前端 + 后端的混合多阶段构建")
print("=" * 60)

fullstack_dockerfile = """
# 阶段 1：构建前端（Node.js）
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --production
#   ↑ npm ci 比 npm install 更快更确定，适合 CI/CD
COPY frontend/ .
RUN npm run build
#   ↑ 产出 dist/ 目录（纯静态 HTML/JS/CSS）

# 阶段 2：构建后端（Python）
FROM python:3.11-slim AS backend-builder
RUN pip install --user --no-cache-dir fastapi uvicorn

# 阶段 3：最终运行镜像
FROM python:3.11-slim

# 从 builder 复制 Python 包
COPY --from=backend-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 从 frontend-builder 复制编译好的静态文件
COPY --from=frontend-builder /frontend/dist /app/static

# 复制后端代码
WORKDIR /app
COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# 最终镜像里：
#  - 没有 Node.js（~200MB 省了）
#  - 没有 npm/node_modules（几百 MB 省了）
#  - 只有 Python 运行时 + 编译好的前端静态文件
# 总体积可能从 1.5GB 降到 300MB
"""

print(fullstack_dockerfile)


# ============================================================
# 示例 3：利用 Docker BuildKit 的缓存挂载加速构建
# ============================================================
print("\n" + "=" * 60)
print("示例 3：BuildKit 缓存挂载")
print("=" * 60)

buildkit_dockerfile = """
# syntax=docker/dockerfile:1
# ↑ 启用 BuildKit 新语法

FROM python:3.11-slim

# --mount=type=cache：挂载一个持久化缓存目录
# pip 下载的包被缓存，下次构建时如果 requirements.txt 没变就跳过下载
RUN --mount=type=cache,target=/root/.cache/pip \\
    pip install --user -r requirements.txt
#   ↑ 第一次构建：正常下载安装（缓存内容写入 /root/.cache/pip）
#   ↑ 第二次构建：如果 requirements.txt 没变，直接复用缓存，闪电完成

# --mount=type=bind：只读挂载文件（构建完后不保留在镜像里）
RUN --mount=type=bind,source=.,target=/src \\
    pip install --user /src
#   ↑ source=. 是宿主机当前目录，target=/src 是容器内目录

# --mount=type=secret：挂载密钥文件（不会留在镜像层里！）
# 适合需要私有 pip 源或 git clone 的场景
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \\
    pip install --user my-private-package
"""

print(buildkit_dockerfile)


# ============================================================
# 示例 4：Python 程序检查自己的容器环境
# ============================================================
print("\n" + "=" * 60)
print("示例 4：检测容器环境")
print("=" * 60)

import os
import platform


def check_container_environment() -> dict:
    """
    检测当前 Python 进程是否在 Docker 容器内运行。
    在容器内运行 `python3 02_multi_stage_build.py` 来验证。

    检测方法（都不是 100% 可靠，但组合使用足够判断）：
    1. /.dockerenv 文件存在 → Docker 会创建这个文件
    2. /proc/1/cgroup 里包含 docker 关键字
    3. /proc/1/sched 里 PID 1 的名字
    """
    result = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "hostname": platform.node(),
        "cwd": os.getcwd(),
    }

    # 方法 1：检查 /.dockerenv
    dockerenv_path = "/.dockerenv"
    if os.path.exists(dockerenv_path):
        result["is_docker"] = True
        result["detection_method"] = ".dockerenv 文件存在"
    else:
        # 方法 2：检查 cgroup
        try:
            with open("/proc/1/cgroup") as f:
                cgroup_content = f.read()
            if "docker" in cgroup_content:
                result["is_docker"] = True
                result["detection_method"] = "cgroup 含 docker 关键字"
            else:
                result["is_docker"] = False
                result["detection_method"] = "未检测到 Docker 特征"
        except FileNotFoundError:
            result["is_docker"] = False
            result["detection_method"] = "非 Linux / 无 /proc 文件系统"

    # 额外信息
    result["cpu_count"] = os.cpu_count()

    # 读取 cgroup 内存限制（容器通常会设 memory limit）
    try:
        with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as f:
            limit = int(f.read().strip())
        if limit < 2**60:  # 小于 1EB 说明真的有限制
            result["memory_limit_mb"] = limit // (1024 * 1024)
    except (FileNotFoundError, ValueError):
        pass

    return result


if __name__ == "__main__":
    info = check_container_environment()
    for key, value in info.items():
        print(f"  {key}: {value}")

    if info.get("is_docker"):
        print("\n✅ 当前运行在 Docker 容器内")
    else:
        print("\n⚠️ 当前不在 Docker 容器内（或无法检测）")
        print("  试着运行: docker run --rm python:3.11-slim python3 02_multi_stage_build.py")


# ============================================================
# 示例 5：Docker 健康检查概念演示
# ============================================================
print("\n" + "=" * 60)
print("示例 5：健康检查（Health Check）概念")
print("=" * 60)

health_check_dockerfile = """
FROM python:3.11-slim

WORKDIR /app
COPY . .

# HEALTHCHECK：Docker 定期执行这个命令来判断容器是否健康
# 格式：HEALTHCHECK [选项] CMD <命令>
HEALTHCHECK \\
    --interval=30s \\
    #   ↑ 每 30 秒检查一次
    --timeout=5s \\
    #   ↑ 单次检查超过 5 秒视为失败
    --start-period=10s \\
    #   ↑ 容器启动后 10 秒内不检查（给应用启动时间）
    --retries=3 \\
    #   ↑ 连续 3 次失败才标记为 unhealthy
    CMD curl -f http://localhost:8000/health || exit 1
    #   ↑ curl -f：HTTP 错误时返回非 0 状态码
    #   ↑ exit 1：告诉 Docker 这次检查失败了

# 健康检查端点（在 FastAPI 里）
# @app.get("/health")
# def health_check():
#     return {"status": "ok", "db": check_db_connection()}
"""

print(health_check_dockerfile)

print("\n✅ 多阶段构建概念演示完成")
print("实际运行需要 Docker 环境：brew install docker (Mac) / apt install docker.io (Linux)")
