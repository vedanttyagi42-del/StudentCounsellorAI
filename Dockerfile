# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# Multi-stage build using openenv-base
# This Dockerfile is flexible and works for both:
# - In-repo environments (with local OpenEnv sources)
# - Standalone environments (with openenv from PyPI/Git)
# The build script (openenv build) handles context detection and sets appropriate build args.

# Use a slim Python image instead of the heavy meta-pytorch base
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY . /app/env
WORKDIR /app/env

RUN pip install --no-cache-dir \
    "openenv-core[core]>=0.2.2" \
    "openai>=1.0.0" \
    "fastapi>=0.115.0" \
    "uvicorn>=0.24.0"

ENV PYTHONPATH="/app/env:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1
ENV ENABLE_WEB_INTERFACE=true

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]