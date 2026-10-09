# ======= Stage 1: Build =======
FROM node:20-alpine AS build

WORKDIR /app

# 先复制依赖声明，利用 Docker 层缓存
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

# 再复制源码，真正构建
COPY . .
RUN npm run build

# ======= Stage 2: Serve =======
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
