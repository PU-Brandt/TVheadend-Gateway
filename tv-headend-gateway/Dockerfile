ARG BUILD_ARCH
FROM ghcr.io/home-assistant/${BUILD_ARCH}-base:latest

RUN apk add --no-cache python3

COPY run.sh /run.sh
COPY addon_server.py /addon_server.py

RUN chmod a+x /run.sh

CMD ["/run.sh"]
