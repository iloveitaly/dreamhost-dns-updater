# Usage:
#   docker build -t dreamhost-dns-updater .

FROM python:3.13.0

LABEL maintainer="Michael Bianco <mike@mikebian.co>"

RUN set -eux; \
  \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    bash \
    nano \
    cron; \
  apt-get clean;

ENV SCHEDULE **None**

COPY . ./

CMD ["bash", "cron.sh"]
