FROM python:3.9-slim AS build
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

FROM python:3.9-slim AS production
WORKDIR /app
COPY --from=build /app /app
RUN pip install --no-cache-dir -r requirements.txt
