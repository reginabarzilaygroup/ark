FROM python:3.6-slim

ENV NAME ark

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN apt-get update -y
RUN apt-get install -y dcmtk

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]
