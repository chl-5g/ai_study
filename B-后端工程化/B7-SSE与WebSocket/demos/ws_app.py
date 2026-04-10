"""
WebSocket 最小示例：回显 + 心跳说明见本章理论稿。

运行（在 demos 目录）：
  pip install fastapi uvicorn
  uvicorn ws_app:app --reload --port 8011

浏览器控制台：
  const ws = new WebSocket('ws://127.0.0.1:8011/ws');
  ws.onmessage = (e) => console.log(e.data);
  ws.send('hi');
"""

from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="B7 WebSocket Demo")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text("server: connected")
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        pass
