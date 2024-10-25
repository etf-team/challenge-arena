FROM nginx:mainline

RUN apt update && apt install openssl -y

RUN mkdir -p /home/web/www

COPY ./config/nginx.conf /etc/nginx/conf.d
COPY ./config/ssl-params.conf /etc/nginx/ssl-params.conf
COPY ./config/*.crt /etc/ssl/certs
COPY ./config/*.key /etc/ssl/certs
