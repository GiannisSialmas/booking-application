# syntax=docker/dockerfile:1

# Base the builder on the official python image (not astral-sh/uv's own python
# base) and copy in just the static `uv` binary. This is the pattern Astral
# (uv's maker) recommends in its own Docker guide: it decouples the choice of
# Python base image from the uv version, so the base stays whatever
# canonical/trusted Python image you'd otherwise use, and uv is layered in as
# a small, independently-cached binary rather than dictating the base image.
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
# type=cache persists uv's package/wheel download cache across builds (not
# baked into the image) so rebuilds don't re-download unchanged deps.
# The two type=bind mounts expose uv.lock/pyproject.toml to this RUN step
# only, instead of a permanent COPY. That scopes this layer's cache key to
# just those two files, so editing main.py alone (COPY'd below, as its own
# layer) doesn't invalidate/re-run the dependency install -- same idea as the
# classic Node "COPY package*.json, npm install, then COPY the rest" pattern.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev
COPY main.py ./

FROM python:3.14-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home --uid 1000 appuser
COPY --from=builder --chown=appuser:appuser /app /app
USER appuser

CMD ["python", "main.py"]
