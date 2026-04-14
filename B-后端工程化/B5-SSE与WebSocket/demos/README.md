# B5 SSE 与 WebSocket — `demos/` 说明

## SSE

```bash
cd demos
pip install fastapi uvicorn
uvicorn sse_app:app --reload --port 8010
curl -N http://127.0.0.1:8010/events
```

生产环境注意：nginx `proxy_buffering off`、`gzip off` 对 SSE 等（见理论稿第 9 节）。

## WebSocket

```bash
uvicorn ws_app:app --reload --port 8011
# 用浏览器 DevTools 或 websocat 连 ws://127.0.0.1:8011/ws
```
