# syntax=docker/dockerfile:1

# --------------------------------------------------------------------
# The web UI, built in its own stage.
#
# node is a BUILD dependency and never a runtime one: nothing from this
# stage reaches the final image except the static files it produces. The
# alternative -- building on a developer machine and committing dist/ --
# makes the image depend on someone remembering to rebuild, which is the
# drift the rest of this project spends effort avoiding.
FROM node:22-slim AS web

WORKDIR /web
COPY web/package.json web/package-lock.json ./
# `npm ci`, not `install`: the lockfile is the point, and ci fails
# loudly on a mismatch instead of quietly resolving something else onto
# a machine nobody is watching.
RUN npm ci --no-audit --no-fund

COPY web/ ./
RUN npm run build


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
# libgomp1 is LightGBM's OpenMP runtime (the ML sizing strategies);
# openssh-client lets the backup service copy an archive off the machine.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential tzdata libgomp1 openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies installed before source code, so an unchanged
# requirements.txt keeps this layer cached across ordinary code edits.
# The warehouse (DuckDB) and ML sets are here because this image is also
# the backtest engine: every backtest reads its bars from the warehouse,
# and the UI offers the ML sizing strategies. The trading loops import
# neither. Fidelity (Playwright) and qlib stay out -- see their files.
COPY requirements.txt requirements-web.txt requirements-warehouse.txt requirements-ml.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -r requirements-web.txt \
        -r requirements-warehouse.txt -r requirements-ml.txt

# Now the actual project. .dockerignore keeps .git, __pycache__, and
# the various tool caches out of the build context and image.
COPY . .

# The built frontend, from the node stage above. server/app.py mounts it
# when index.html is present and serves the API alone when it is not, so
# this COPY is the single thing that turns the API into a full
# deployment -- and it means ONE origin in production, with no CORS
# involved at all.
COPY --from=web /web/dist ./web/dist

# Runs as a non-root user -- nothing here needs root, and the container
# may hold live Alpaca credentials in its environment at runtime.
#
# Every mount point docker-compose.yml uses exists here, owned by runner:
# a named volume takes its owner from the first container that mounts it,
# and one first mounted at a path the image lacks comes up root-owned --
# a ledger the trading loop could then not write.
RUN useradd --create-home --uid 1000 runner \
    && mkdir -p /app/state /app/state-ultimate /app/state-production /app/state-fidelity \
        /app/data /app/config /app/output /app/warehouse /app/backups \
        /app/control /app/controls/paper-ultimate /app/controls/paper /app/controls/live \
        /app/controls/fidelity \
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


# --------------------------------------------------------------------
# The research image: the app plus qlib (requirements-qlib.txt's pyqlib)
# for the training tools that may use it -- tools/train_qlib_regime.py
# --use-qlib. Its own target, never the deployed one: ~200 packages
# (mlflow, cvxpy, gym, ...) that the trading loops and the server never
# import. pyqlib publishes nothing for Python 3.14, which is why this is
# an image and not the workstation's .venv. rdagent, the file's other
# entry, is an LLM agent loop and is not installed.
#
#     docker compose run --rm research tools/train_qlib_regime.py ...
FROM base AS research
USER root
# qlib's concept-drift modules (qlib.contrib.meta, what --use-qlib checks
# for) import torch, which pyqlib does not declare. The CPU build is enough.
RUN pip install --no-cache-dir "pyqlib>=0.9.6" \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
USER runner


# The deployed image, and the default target -- the last stage is what a
# bare `docker build .` produces: the app without qlib.
FROM base AS app
# Which commit it was built from, when the build says so (docker-compose.yml
# passes VAI_BUILD_COMMIT through): the image has no .git, and the Live page's
# Deployment card shows this beside the code's fingerprint
# (engine/core/build_info.py). Last, so a new commit rebuilds one layer.
ARG VAI_BUILD_COMMIT=
ENV VAI_BUILD_COMMIT=${VAI_BUILD_COMMIT}
