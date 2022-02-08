FROM python:3.8 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels/ -r requirements.txt git+git://github.com/harrivle/Mirai.git@v0.4.1

FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    dcmtk \
    python3-sklearn-lib \
&& rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels/

COPY . .

ENV NAME ark

EXPOSE 5000

ENTRYPOINT ["python", "main.py"]
