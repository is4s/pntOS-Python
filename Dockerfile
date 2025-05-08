FROM ubuntu:24.04

# Install dependencies needed to bring in upstream projects via their source
RUN apt update && apt install git -y

# Install dependencies needed to run LCM.
RUN apt update && apt install libglib2.0-dev -y

# Install dependencies needed to install Rye.
RUN apt update && apt install curl -y

# Install Rye
ENV PATH=/root/.rye/shims:$PATH
RUN curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash

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
