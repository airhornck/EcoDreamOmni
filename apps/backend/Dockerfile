# Backend Dockerfile — optimized for layer caching + China network
# 默认配置为国内高速源（清华 TUNA），开箱即用

ARG PIP_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
ARG APT_MIRROR="mirrors.tuna.tsinghua.edu.cn"

# ── Builder stage ──
FROM python:3.11-slim AS builder

ARG PIP_INDEX_URL
ARG APT_MIRROR

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH

# Configure apt mirror (optional)
RUN if [ -n "$APT_MIRROR" ]; then \
      sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
      sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list; \
    fi

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install with mirror support, timeout, and retries
RUN pip config set global.timeout 120 && \
    pip config set global.retries 5 && \
    if [ -n "$PIP_INDEX_URL" ]; then \
      pip install --user --no-cache-dir -i "$PIP_INDEX_URL" -r requirements.txt; \
    else \
      pip install --user --no-cache-dir -r requirements.txt; \
    fi

# ── Production stage ──
FROM python:3.11-slim

ARG APT_MIRROR

WORKDIR /app

# Configure apt mirror (optional)
RUN if [ -n "$APT_MIRROR" ]; then \
      sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
      sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list; \
    fi

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY pytest.ini .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]