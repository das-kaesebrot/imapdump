FROM python:alpine

ENV PYTHONUNBUFFERED=true
ARG IMAPDUMP_DIRECTORY=/var/opt/imapdump

RUN adduser -u 1100 -D imapdump

RUN mkdir -pv ${IMAPDUMP_DIRECTORY}
RUN chown -R 1100:1100 ${IMAPDUMP_DIRECTORY}

COPY --chown=1100:1100 . ${IMAPDUMP_DIRECTORY}

WORKDIR ${IMAPDUMP_DIRECTORY}

VOLUME [ "${IMAPDUMP_DIRECTORY}/config" ]

RUN python -m pip install -r requirements.txt

USER imapdump

CMD [ "/usr/bin/env", "python3", "-m", "src.imapdump" ]