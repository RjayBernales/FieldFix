FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend FIELDFIX_PROVIDER=mock FIELDFIX_HOSTED_DATA_DIR=/app/.data/hosted PORT=10000
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock && useradd --create-home --uid 10001 fieldfix && mkdir -p /app/.data && chown fieldfix:fieldfix /app/.data
COPY backend/app ./backend/app
COPY --from=frontend /build/dist ./frontend/dist
USER fieldfix
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn app.hosted:create_hosted_app --factory --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --no-proxy-headers"]
