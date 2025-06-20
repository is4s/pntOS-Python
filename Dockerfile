FROM ubuntu:24.04

# Optional TOKEN_URL from CI
ARG TOKEN_URL

# Install dependencies needed to bring in upstream projects via their source
RUN apt update && apt install git -y

# Install python, and everything it needs to create a virtual environment.
RUN apt update && apt install python3 python3-venv -y

# Install dependencies needed to run LCM.
RUN apt update && apt install libglib2.0-dev -y

# Install dependencies needed to install uv.
RUN apt update && apt install curl -y

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_UNMANAGED_INSTALL="/usr/local/bin" bash

# Install java (needed to run app)
RUN apt update && apt install default-jre-headless -y

# Install make (needed to build docs)
RUN apt update && apt install make -y

# If in CI, rewrite SSH URLs
RUN bash -c \ 
'if [[ -n $TOKEN_URL ]]; then \
  echo -e \
  "[url \"$TOKEN_URL\"]\n\tinsteadOf = git@git.aspn.us:\n\tinsteadOf = ssh://git@git.aspn.us/" \
  > /root/.gitconfig; \
fi'

WORKDIR /work
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/bin/bash"]
# Prepend future venv path to PATH so that pip automatically uses it.
ENV PATH=/work/.venv/bin:$PATH
ENV VIRTUAL_ENV=/work/.venv
