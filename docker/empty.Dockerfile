FROM python:3.8 AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ wget unzip \
    && rm -rf /var/lib/apt/lists/*

COPY ../requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels/ -r requirements.txt

FROM python:3.8-slim

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels/

COPY .. .

ENV NAME ark

EXPOSE 5000

ENTRYPOINT ["python", "main.py", "--config", "api/configs/empty.json"]
