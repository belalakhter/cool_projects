# Base Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# System dependencies (add others if needed)
RUN apt-get update && apt-get install -y curl && apt-get clean

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml poetry.lock /app/

# Install dependencies using Poetry (no dev dependencies)
RUN poetry install --no-root

# Copy the rest of the code
COPY . /app/

# Entrypoint for your app
CMD ["poetry", "run", "python", "-u", "-m", "src.agent.main"]
