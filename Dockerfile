# syntax=docker/dockerfile:1

# =======================================================
# Stage 1: Build Next.js Frontend
# =======================================================
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY package.json package-lock.json ./
RUN npm ci

COPY src/ ./src/
COPY public/ ./public/
COPY next.config.ts tsconfig.json postcss.config.mjs eslint.config.mjs next-env.d.ts ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# =======================================================
# Stage 2: Final Unified Production Runner
# =======================================================
FROM python:3.11-slim AS runner
WORKDIR /app

# Install system dependencies: FFmpeg & ffprobe, DejaVu TTF fonts, libpq, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Node.js runtime from official Debian-based Node image (no apt-get bloat)
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node:22-bookworm-slim /usr/local/bin/npm /usr/local/bin/npm
COPY --from=node:22-bookworm-slim /usr/local/bin/npx /usr/local/bin/npx

# Install Python backend dependencies
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Install frontend production dependencies only
COPY package.json package-lock.json /app/frontend/
RUN cd /app/frontend && npm ci --omit=dev && npm cache clean --force

# Copy Next.js production build artifacts from builder stage
COPY --from=frontend-builder /app/frontend/.next /app/frontend/.next
COPY --from=frontend-builder /app/frontend/public /app/frontend/public

# Copy backend source code
COPY backend/ /app/backend/

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production
ENV PORT=3000
ENV NEXT_TELEMETRY_DISABLED=1

# Expose Web UI (3000) and Backend API (8000)
EXPOSE 3000
EXPOSE 8000

# Health check against backend
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
