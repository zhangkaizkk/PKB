FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

RUN mkdir -p /app/data/files /app/data/tmp

EXPOSE 8000
