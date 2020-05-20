# Pull base image
FROM turbosnute/python3-rpi

# Labels
LABEL MAINTAINER="Øyvind Nilsen <oyvind.nilsen@gmail.com>"

# RUN pip install setuptools
RUN pip3 install pyTibber influxdb

# Copy files
ADD tibberinfo.py /
ADD get.sh /

# Environment vars
ENV PYTHONIOENCODING=utf-8

# Run
CMD ["/bin/bash","/get.sh"]
