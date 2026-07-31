# Backend-only container -- the frontend deploys separately to Vercel via
# its own native build (no Docker needed there). Build context is the
# REPO ROOT, not backend/, because backend/ imports poker/ as a sibling
# package -- both need to be present in the image.
#
# Build & run locally:
#   docker build -t kelly-poker-backend .
#   docker run -p 8000:8000 -e DATABASE_URL=postgresql://... kelly-poker-backend
#
# Matches the local venv's Python version (3.13.9).
FROM python:3.13-slim

WORKDIR /app

# Installing requirements before copying the rest of the source lets
# Docker cache this layer across rebuilds that only change application
# code, not dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY poker/ ./poker/
COPY backend/ ./backend/

# requirements.txt is deliberately NOT split into a prod-only file --
# one source of truth matches this project's "simplicity first"
# convention, at the cost of also installing pytest/matplotlib/pre-commit
# into the production image. Acceptable trade-off at this project's scale.

# Render (and most PaaS hosts) inject PORT at runtime; default to 8000
# for local `docker run`. Shell form (not exec form) so $PORT expands.
ENV PORT=8000
EXPOSE 8000
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
