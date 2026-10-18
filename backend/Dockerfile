FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app XINXIN_DATA_DIR=/var/lib/xinxin XINXIN_TASK_CONCURRENCY=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/var/lib/xinxin/matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client fonts-wqy-zenhei ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY app ./app
COPY vendor ./vendor
COPY resources ./resources
COPY scripts ./scripts
COPY THIRD_PARTY.md ./
RUN useradd --uid 10001 --create-home xinxin && mkdir -p /var/lib/xinxin && chown -R xinxin:xinxin /var/lib/xinxin
USER xinxin
WORKDIR /var/lib/xinxin
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*", "--no-access-log"]
