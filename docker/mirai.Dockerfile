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
ARG MODEL_COMMIT=v0.8.0
ARG SNAPSHOT_URL=https://github.com/reginabarzilaygroup/Mirai/releases/download/v0.8.0/snapshots.zip
RUN git clone https://github.com/reginabarzilaygroup/Mirai.git
RUN pip install --no-cache-dir --disable-pip-version-check git+https://github.com/reginabarzilaygroup/Mirai.git@${MODEL_COMMIT}

# Copy server code
COPY . .

# Download trained model weights
RUN wget "${SNAPSHOT_URL}" -O /tmp/snapshots.zip \
&& mkdir -p models/snapshots && unzip -o -d models/snapshots/ /tmp/snapshots.zip

ENV NAME ark

EXPOSE 5000 8000

ENV ARK_CONFIG api/configs/mirai.json
ENV LOG_LEVEL "INFO"
ENV ARK_THREADS 4
ENTRYPOINT gunicorn \
--bind 0.0.0.0:5000 \
--timeout 0 \
--threads $ARK_THREADS \
--log-level $LOG_LEVEL \
--access-logfile - \
"main:create_app()"
