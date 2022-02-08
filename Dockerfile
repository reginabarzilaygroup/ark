FROM python:3.8 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    wget \
    unzip \
&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels/ -r requirements.txt git+git://github.com/harrivle/Mirai.git@v0.4.1

RUN wget --load-cookies /tmp/cookies.txt \
    "https://drive.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://drive.google.com/uc?export=download&id=1OLCjciwoZ51cpVmE_Dw6ULhWYYf577lm' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1OLCjciwoZ51cpVmE_Dw6ULhWYYf577lm" \
    -O /tmp/snapshots.zip \
&& unzip -d /snapshots/ /tmp/snapshots.zip

FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    dcmtk \
    python3-sklearn-lib \
&& rm -rf /var/lib/apt/lists/*

COPY --from=builder /snapshots models/snapshots/
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels/

COPY . .

ENV NAME ark

EXPOSE 5000

ENTRYPOINT ["python", "main.py"]
