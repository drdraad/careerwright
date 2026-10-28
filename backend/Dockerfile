# One image for the API, the DBOS worker, setup commands and the loopback edge. Installs the
# locked dependency set only (uv.lock); the build is the only step that needs the network.
FROM python:3.12.16-slim-bookworm@sha256:6dd8b6dab6b3adc7812bab69eca5dbdc1a5cc690ad28306d234ffb4ef8ac9753

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYDANTIC_AI_NO_BANNER=1 \
    PATH=/opt/venv/bin:$PATH

RUN pip install --no-cache-dir uv==0.9.18
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin nessa

USER nessa
