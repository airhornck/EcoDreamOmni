# Frontend Dockerfile for EcoDreamOmni
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies in Linux container
COPY package*.json .
RUN npm ci

# Copy source (local node_modules may be brought in from Windows host)
COPY . .

# Remove host-side node_modules and reinstall to ensure Linux-compatible binaries
RUN rm -rf node_modules && npm ci

# Build
RUN npm run build

# Production stage with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
