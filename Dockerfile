FROM python:3.6-alpine

LABEL maintainer="Jiewei Qian <qjw@wacky.one>"
LABEL upstream="zsnmwy <szlszl35622@gmail.com>"

ENV LIBRARY_PATH=/lib:/usr/lib \
    TZ="Asia/Shanghai" \
    USER_NAME='' \
    USER_PASSWORD=''

WORKDIR /app

RUN apk add --no-cache git tzdata && \
    cp /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo ${TZ} > /etc/timezone && \
    git clone https://github.com/wacky6/bilibili-live-tools.git /app && \
    pip install -r requirements.txt && \
    rm -r /var/cache/apk && \
    rm -r /usr/share/man && \
    cp /app/READ_SAMPLE_CONF.toml /app/conf/user.toml

ENTRYPOINT git pull -f && \
            pip install -r requirements.txt && \
            sed -i ''"$(cat conf/bilibili.toml -n | grep "username =" | awk '{print $1}')"'c '"$(echo "username = \"${USER_NAME}\"")"'' conf/bilibili.toml && \
            sed -i ''"$(cat conf/bilibili.toml -n | grep "password =" | awk '{print $1}')"'c '"$(echo "password = \"${USER_PASSWORD}\"")"'' conf/bilibili.toml && \
            python ./run.py