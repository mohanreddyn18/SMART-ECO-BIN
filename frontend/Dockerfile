# ==============================================================================
# SMART ECO BIN — Frontend Production Dockerfile (Google Cloud Run Ready)
# Multi-stage build: Vite build -> Unprivileged Nginx SPA static server
# ==============================================================================

FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Optional build-time API base URL injection
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ------------------------------------------------------------------------------
# Production Nginx Serving Stage
# ------------------------------------------------------------------------------
FROM nginxinc/nginx-unprivileged:alpine-slim

# Copy built frontend assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud Run dynamic port binding
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8080/nginx-health || exit 1

CMD ["nginx", "-g", "daemon off;"]
