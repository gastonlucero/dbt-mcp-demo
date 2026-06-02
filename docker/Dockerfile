FROM python:3.13.3-alpine3.21

WORKDIR /app

ENV PYTHONPATH=/app \
  PYTHONUNBUFFERED=1

RUN adduser --disabled-password --no-create-home appuser

# Upgrade pip to avoid issues with older Alpine-bundled versions
RUN pip install --no-cache-dir --upgrade pip

# Copy only the manifest first — pip install . uses it for layer caching.
# When src/ is absent setuptools auto-discovery finds no packages but still
# resolves and installs all declared dependencies, which is exactly what we
# want for the cache layer.
COPY --chown=appuser:appuser mcp-server/pyproject.toml .

# Install production dependencies from pyproject.toml
RUN pip install --no-cache-dir .

# Install pytest for testing
RUN pip install --no-cache-dir pytest>=8.0

COPY --chown=appuser:appuser mcp-server/src/ ./src/
COPY --chown=appuser:appuser mcp-server/tests/ ./tests/

# Health check using the /health endpoint (returns 200 OK if service is healthy)
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9001/health', timeout=3).read()" || exit 1

USER appuser

EXPOSE 9001

CMD ["python", "src/server.py"]