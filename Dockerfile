# ---- frontend build ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps
COPY frontend/ ./
ENV REACT_APP_API_URL=
RUN npm run build

# ---- backend ----
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend /fe/build ./frontend/build
ENV PORT=10000
EXPOSE 10000
# Shell form so $PORT from Render is expanded. Bind 0.0.0.0 so the port scan succeeds.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
