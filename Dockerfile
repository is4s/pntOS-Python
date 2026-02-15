FROM ros:jazzy-ros-base

# Install container dependencies
RUN apt update && apt install -y \
    # For cloning upstream projects
    git \
    ssh \
    # For installing uv
    curl \
    # For running cobra
    python3 \
    python3-venv \
    # For running LCM
    libglib2.0-dev \
    # Java, for running LCM
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_UNMANAGED_INSTALL="/usr/local/bin" bash

WORKDIR /work
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/bin/bash"]
# Prepend future venv path to PATH so that pip automatically uses it.
ENV PATH=/work/.venv/bin:$PATH
ENV VIRTUAL_ENV=/work/.venv
