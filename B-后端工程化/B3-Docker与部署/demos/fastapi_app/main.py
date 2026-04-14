"""B5 Docker demo：最小 FastAPI，供镜像内运行。"""

from fastapi import FastAPI

app = FastAPI(title="B5 Docker Demo")


@app.get("/health")
def health():
    return {"status": "ok"}
