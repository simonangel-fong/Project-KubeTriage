FROM ubuntu:24.04

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Toronto \
    DEBIAN_FRONTEND=noninteractive \
    WORKER=2 \
    VENV_PATH=/opt/venv \
    APISERVER=https://kubernetes.default.svc \
    SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount \
    TOKEN_FILE=/var/run/secrets/kubernetes.io/serviceaccount/token \
    NAMESPACE_FILE=/var/run/secrets/kubernetes.io/serviceaccount/namespace \
    CACERT_FILE=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tzdata \
        curl \
        python3 \
        python3-pip \
        python3-venv && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

WORKDIR /app

COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

RUN useradd -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--http", "httptools"]