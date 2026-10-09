FROM python:3.11-slim-bookworm

WORKDIR /app

# Aliyun apt mirror + PaddleOCR system deps
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

RUN mkdir -p /app/data/files /app/data/tmp /app/data/chroma

EXPOSE 8000
