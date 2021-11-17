FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gcc python3-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install -U pip && pip install -r requirements.txt

ADD . /app

EXPOSE 8000
