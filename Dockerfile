# syntax=docker/dockerfile:1

# Base image matches pyproject.toml's requires-python floor exactly
# (>=3.12) -- this is not a rounded-up default, it is the same version
# constraint the project itself declares.
FROM python:3.12-slim AS base

# Runtime-only dependencies for compiling any C-extension wheels that
# lack prebuilt binaries for this platform (pandas/numpy usually ship
# manylinux wheels, but this keeps the build resilient rather than
# hoping). Removed from the final layer via a multi-stage-style cleanup
# below is unnecessary here since apt lists are purged and this layer
# is small; kept minimal on purpose.
# tzdata is installed at the SYSTEM level here AND via pip in
# requirements.txt, and the duplication is deliberate: the pip package
# satisfies Python's zoneinfo, the system one makes the TZ environment
# variable and any non-Python tool agree with it. On a slim image
# neither is present, and ZoneInfo("America/New_York") raises at import
# -- which on a Pi surfaces as a container exiting instantly with a
# traceback that no market-hours logic ever reached.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies installed before source code, so an unchanged
# requirements.txt keeps this layer cached across ordinary code edits.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Now the actual project. .dockerignore keeps .git, __pycache__, and
# the various tool caches out of the build context and image.
COPY . .

# Runs as a non-root user -- nothing here needs root, and the container
# may hold live Alpaca credentials in its environment at runtime.
RUN useradd --create-home --uid 1000 runner \
    && mkdir -p /app/state /app/data /app/config /app/output \
    && chown -R runner:runner /app
USER runner

# Where persistent state (Task 7.3's SQLite ledger, Task 7.14's audit
# log) is expected to live. Mount a volume here so state survives a
# container restart -- the entire point of Task 7.3/7.12's design.
VOLUME ["/app/state"]

ENTRYPOINT ["python", "cli.py"]
# No subcommand by default: `docker run <image>` alone prints usage
# rather than silently doing nothing or guessing what to run.
CMD ["--help"]
