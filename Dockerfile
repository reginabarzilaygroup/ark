FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    dcmtk \
    g++ \
&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade --no-cache-dir setuptools -r requirements.txt

COPY . .

ENV NAME ark

EXPOSE 5000

ENTRYPOINT ["python", "main.py"]
