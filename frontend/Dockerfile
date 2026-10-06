FROM nginx:alpine

# 前端在宿主机已 npm run build 好 dist/，这里直接 COPY 进去
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
