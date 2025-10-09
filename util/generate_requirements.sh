#!/usr/bin/env bash

uv export --frozen --no-hashes -o requirements.txt
uv export --frozen --no-dev --no-hashes -o requirements-minimal.txt
