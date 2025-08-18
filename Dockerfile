FROM python:3.11-slim

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Copy Poetry files first for better caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only=main --no-root

# Copy application code
COPY . ./

# Run with uvicorn, using Cloud Run's PORT environment variable
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
