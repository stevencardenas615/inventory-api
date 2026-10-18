FROM python:3.14-slim

# uv, copied from its official image (no pip install needed)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install dependencies first, so this layer is cached until pyproject/uv.lock change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then the application code
COPY app ./app

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
