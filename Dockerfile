FROM python:3.6-slim

ENV NAME ark

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
COPY api api
COPY model model

EXPOSE 5000

CMD python main.py
