# ---------- build frontend ----------
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# allow API endpoint override at build time
ARG VITE_API_URL=http://127.0.0.1:8010/api/send
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# ---------- serve static with nginx ----------
FROM nginx:1.27-alpine AS runner
WORKDIR /usr/share/nginx/html
COPY --from=frontend /app/frontend/dist/ ./

# Minimal SPA-friendly config
RUN rm -f /etc/nginx/conf.d/default.conf
COPY ./config/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
