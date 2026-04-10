"""
SSE 最小示例：text/event-stream

运行（在 demos 目录）：
  pip install fastapi uvicorn
  uvicorn sse_app:app --reload --port 8010

消费：
  curl -N http://127.0.0.1:8010/events
"""

from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(title="B7 SSE Demo")


@app.get("/events")
async def events():
    async def gen():
        for i in range(8):
            await asyncio.sleep(0.25)
            payload = json.dumps({"chunk": i}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
def health():
    return {"ok": True}
