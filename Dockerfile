FROM ubuntu:24.04

# Install dependencies needed to bring in upstream projects via their source
RUN apt update && apt install git -y

# Install dependencies needed to run LCM.
RUN apt update && apt install libglib2.0-dev -y

# Install dependencies needed to install Uv.
RUN apt update && apt install curl -y

# Install Uv
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_UNMANAGED_INSTALL="/usr/local/bin" bash

# Install java (needed to run app)
RUN apt update && apt install default-jre-headless -y

# Install make (needed to build docs)
RUN apt update && apt install make -y

WORKDIR /work
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/bin/bash"]
# Prepend future venv path to PATH so that pip automatically uses it.
ENV PATH=/work/.venv/bin:$PATH
ENV VIRTUAL_ENV=/work/.venv
