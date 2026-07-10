FROM nginx:1.29-alpine
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY proxy-headers.conf proxy-websocket.conf real-ip.conf /etc/nginx/conf.d/
CMD ["nginx", "-g", "daemon off;"]
