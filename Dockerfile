FROM python:3.11-slim

# Avoid .pyc files and enable unbuffered output (better logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir ismr-downloader

VOLUME ["/app"]

ENTRYPOINT ["ismr-downloader"]