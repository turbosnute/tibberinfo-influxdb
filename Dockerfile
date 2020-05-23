# Pull base image
FROM ubuntu:latest

# Labels
LABEL MAINTAINER="Øyvind Nilsen <oyvind.nilsen@gmail.com>"

# Setup external package-sources
RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python3-wheel \
    python3-setuptools \
    python3-pip \
    gcc \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
# RUN pip install
RUN pip3 install pyTibber influxdb arrow

# Copy files
ADD tibberinfo.py /
ADD get.sh / 

# Chmod
RUN chmod 755 /get.sh
RUN chmod 755 /tibberinfo.py

# Environment vars
ENV PYTHONIOENCODING=utf-8

# Run
CMD ["/bin/bash","/get.sh"]
