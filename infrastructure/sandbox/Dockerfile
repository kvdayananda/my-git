FROM python:3.11-slim@sha256:673719e071ecf27434fd2635bbd8d00f49f4fdd81f243143438a42ced8bedf60

RUN groupadd --system --gid 1000 sandbox \
    && useradd --system --uid 1000 --gid 1000 --create-home sandbox \
    && python -m pip install --no-cache-dir --disable-pip-version-check pytest==8.3.5
USER 1000:1000
WORKDIR /workspace
ENTRYPOINT ["pytest"]
