FROM docker:latest as static-docker-source

FROM python:3-alpine

COPY --from=static-docker-source /usr/local/bin/docker /usr/local/bin/docker

RUN apk add git

COPY . /tmp/
RUN apk add --no-cache --virtual .python-builddeps gcc g++ rust libc-dev libffi-dev openssl-dev cargo \
    && pip install /tmp/ \
    && apk del .python-builddeps
RUN mkdir -p /etc/localbinder/ && cp /tmp/config/localbinder-config.py /etc/localbinder/

ENTRYPOINT ["python", "-m", "localbinder", "-f", "/etc/localbinder/localbinder-config.py"]
