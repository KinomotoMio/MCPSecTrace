FROM ghcr.io/astral-sh/uv:0.7.13-python3.13-bookworm

WORKDIR /app

COPY . /app

ENV PYTHONUNBUFFERED=1
RUN uv sync

CMD []


ENTRYPOINT [ "./docker-entrypoint.sh" ]
