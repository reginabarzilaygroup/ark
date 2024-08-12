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
ARG MODEL_COMMIT=v0.12.0
RUN pip install --no-cache-dir --disable-pip-version-check \
    git+https://github.com/reginabarzilaygroup/Mirai.git@${MODEL_COMMIT}

# Download trained model weights
RUN mirai-predict --dry-run

# Copy and install server code
ARG ARK_COMMIT=v0.6.2
RUN git clone https://github.com/reginabarzilaygroup/ark.git
RUN cd ark && git checkout ${ARK_COMMIT} \
    && pip install --no-cache-dir --disable-pip-version-check -e .

WORKDIR /app/ark
ENV NAME=ark

EXPOSE 5000 8000

ENV LOG_LEVEL="INFO"
ENV ARK_THREADS=4
ENTRYPOINT ark-run mirai
