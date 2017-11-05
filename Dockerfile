FROM python:alpine

WORKDIR /var/www/python/host_reg

COPY requirements.txt .
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories
RUN apk add --no-cache --update hiredis \
    && pip install --no-cache-dir -r requirements.txt

COPY [ "host.py", "main.py", "logging.conf", "./" ]

EXPOSE 8888/tcp

ENTRYPOINT [ "/var/www/python/host_reg/main.py" ]