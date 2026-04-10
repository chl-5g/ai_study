# B5 示例：单阶段构建（学习用）。生产请改用非 root、多阶段等（见本章理论稿第 7、13 节）
FROM python:3.12-slim

WORKDIR /app

COPY fastapi_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fastapi_app/ ./fastapi_app/

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
