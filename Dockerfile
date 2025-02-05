# Build ARGS
ARG ARCH=

# Pull base image
FROM python:3.12-alpine

# Labels
LABEL MAINTAINER="Øyvind Nilsen <oyvind.nilsen@gmail.com>"

# Environment vars
ENV PYTHONIOENCODING=utf-8
ENV USER_ID=65535
ENV GROUP_ID=65535
ENV USER_NAME=tibber
ENV GROUP_NAME=tibber

WORKDIR /app

RUN addgroup -g $GROUP_ID $GROUP_NAME && \
    adduser --shell /sbin/nologin --disabled-password \
    --no-create-home --uid $USER_ID --ingroup $GROUP_NAME $USER_NAME

# Copy files
ADD tibberinfo.py /app/
ADD get.sh /app/
ADD requirements.txt /app/
ADD pyproject.toml /app/
ADD README.md /app/

# Chmod
RUN chmod 755 /app/get.sh
RUN chmod 755 /app/tibberinfo.py

RUN apk add --update --no-cache --virtual .tmp-build-deps gcc libc-dev
RUN pip install --no-cache-dir -r requirements.txt
RUN apk del .tmp-build-deps

USER $USER_NAME

CMD ["/bin/sh","/app/get.sh"]
