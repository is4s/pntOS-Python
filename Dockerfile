FROM ubuntu:24.04

# Install dependencies needed to install Rye and mypy.
RUN apt update && apt install python3-pip curl git -y

# Install Rye
ENV PATH=/root/.rye/shims:$PATH
RUN curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash

# Install mypy
RUN pip install mypy --break-system-packages

WORKDIR /work
ENTRYPOINT ["/bin/bash", "-c"]
