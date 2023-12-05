FROM python:3.8 AS builder

# Build python dependencies as wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ wget unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels/ -r requirements.txt

FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    dcmtk python3-sklearn-lib git \
&& rm -rf /var/lib/apt/lists/*

# Download trained model
RUN wget --load-cookies /tmp/cookies.txt \
    "https://drive.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://drive.google.com/uc?export=download&id=1O2IL_SlZhCtvTyiBG8CKFcuZsIvp4Qng' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1O2IL_SlZhCtvTyiBG8CKFcuZsIvp4Qng" \
    -O /tmp/snapshots.zip \
&& unzip -d models/snapshots/ /tmp/snapshots.zip

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels/

# Install model code
RUN git clone https://github.com/reginabarzilaygroup/Mirai.git
RUN pip install --no-cache-dir --disable-pip-version-check git+https://github.com/reginabarzilaygroup/Mirai.git@v0.6.0

COPY . .

ENV NAME ark

EXPOSE 5000

ENTRYPOINT ["python", "main.py", "--config", "api/configs/mirai.json"]
