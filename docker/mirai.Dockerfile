FROM python:3.8 AS builder

# Build python dependencies as wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels/ -r requirements.txt

FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    dcmtk python3-sklearn-lib git wget unzip \
&& rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels/

# Copy/Install model code
RUN git clone https://github.com/reginabarzilaygroup/Mirai.git
RUN pip install --no-cache-dir --disable-pip-version-check git+https://github.com/reginabarzilaygroup/Mirai.git@v0.6.0

# Copy server code
COPY . .

# Download trained model weights
RUN wget 'https://github.com/reginabarzilaygroup/Mirai/releases/latest/download/snapshots.zip' -O /tmp/snapshots.zip \
&& mkdir -p models/snapshots && unzip -o -d models/snapshots/ /tmp/snapshots.zip

ENV NAME ark

EXPOSE 5000

ENTRYPOINT ["python", "main.py", "--config", "api/configs/mirai.json"]
