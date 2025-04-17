# Build stage
FROM python:3.9-slim AS build

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Final stage
FROM python:3.9-slim

WORKDIR /app

COPY --from=build /app /app

CMD ["python", "main.py"]
