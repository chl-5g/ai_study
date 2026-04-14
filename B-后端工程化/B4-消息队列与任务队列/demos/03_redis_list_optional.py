"""
03_redis_list_optional.py — Redis 列表当简易队列：LPUSH + BRPOP。

运行：python3 03_redis_list_optional.py
需要：本机 redis-server 监听 6379，且 pip install redis
"""

from __future__ import annotations

KEY = "b6:demo:queue"


def main() -> None:
    try:
        import redis
    except ImportError:
        print("跳过：pip install redis")
        return

    r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    try:
        r.ping()
    except redis.ConnectionError as e:
        print(f"跳过：连不上 Redis ({e})")
        return

    r.delete(KEY)
    r.lpush(KEY, "msg-a", "msg-b")
    r.lpush(KEY, "msg-c")
    print("入队完成，依次阻塞弹出:")
    for _ in range(3):
        item = r.brpop(KEY, timeout=2)
        print(" ", item)


if __name__ == "__main__":
    main()
