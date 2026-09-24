# ---- build stage ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# The SPA calls the API via a same-origin /api path; nginx proxies it (see nginx.conf).
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

# ---- serve stage ----
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
