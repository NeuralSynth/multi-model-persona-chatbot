# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: dependency builder
# Compiles wheels in an isolated stage so the final image has no build tools.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build essentials only in this stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build wheels into /wheels — copied into final stage, no pip cache
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: final runtime image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install wheels from builder (no gcc, no pip cache)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

# Copy application source
COPY personas/ ./personas/
COPY core/     ./core/
COPY assets/   ./assets/
COPY app.py    .
COPY main.py   .

# Streamlit config — disable telemetry, set port/address
RUN mkdir -p /app/.streamlit
COPY .streamlit/config.toml .streamlit/config.toml

# Switch to non-root
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check — confirms the app is serving
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

# Entry point
ENTRYPOINT ["python", "main.py"]
