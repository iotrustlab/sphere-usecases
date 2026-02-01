# OpenPLC Runtime Container for SPHERE CPS
# Based on the official OpenPLC Dockerfile with modifications for automated deployment
#
# This builds on the official OpenPLC setup which uses Debian Trixie (Python 3.12+)
# and installs all capabilities: DNP3, Snap7, libmodbus
#
# Version pinning:
#   Build args allow pinning to a specific OpenPLC commit or branch.
#   Default is 'master' but scenarios can override with a specific commit SHA.

FROM debian:trixie-20251020

# OpenPLC version - can be a branch name, tag, or commit SHA
ARG OPENPLC_VERSION=master
ARG OPENPLC_REPO=https://github.com/thiagoralves/OpenPLC_v3.git

# Install git first to clone the repo
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone OpenPLC at specific version
WORKDIR /workdir
RUN git clone ${OPENPLC_REPO} . && \
    git checkout ${OPENPLC_VERSION}

# Record the exact commit for reproducibility
RUN git rev-parse HEAD > /workdir/.git-commit

# Create persistent directory for docker mode
RUN mkdir -p /docker_persistent

VOLUME /docker_persistent

# Run the official OpenPLC docker installation
# This installs all dependencies, compiles MatIEC, DNP3, Snap7, libmodbus
RUN ./install.sh docker

# Setup persistent storage symlinks (from official Dockerfile)
RUN touch /docker_persistent/mbconfig.cfg && \
    touch /docker_persistent/persistent.file && \
    mkdir -p /docker_persistent/st_files && \
    cp /workdir/webserver/openplc.db /docker_persistent/openplc.db && \
    mv /workdir/webserver/openplc.db /workdir/webserver/openplc_default.db && \
    cp /workdir/webserver/dnp3.cfg /docker_persistent/dnp3.cfg && \
    mv /workdir/webserver/dnp3.cfg /workdir/webserver/dnp3_default.cfg && \
    cp -r /workdir/webserver/st_files/ /docker_persistent/st_files/ && \
    mv /workdir/webserver/st_files /workdir/webserver/st_files_default && \
    cp /workdir/webserver/active_program /docker_persistent/active_program && \
    mv /workdir/webserver/active_program /workdir/webserver/active_program_default && \
    ln -sf /docker_persistent/mbconfig.cfg /workdir/webserver/mbconfig.cfg && \
    ln -sf /docker_persistent/persistent.file /workdir/webserver/persistent.file && \
    ln -sf /docker_persistent/openplc.db /workdir/webserver/openplc.db && \
    ln -sf /docker_persistent/dnp3.cfg /workdir/webserver/dnp3.cfg && \
    ln -sf /docker_persistent/st_files /workdir/webserver/st_files && \
    ln -sf /docker_persistent/active_program /workdir/webserver/active_program

# Copy our custom entrypoint for automated program loading
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Store version info for debugging
RUN echo "OPENPLC_VERSION=${OPENPLC_VERSION}" > /workdir/version.txt && \
    cat /workdir/.git-commit >> /workdir/version.txt 2>/dev/null || true

# Expose ports
# 8080: Web interface
# 502: Modbus TCP
EXPOSE 8080 502

# Environment variables for automated deployment
ENV OPENPLC_PROGRAM=/programs/program.st
ENV OPENPLC_MODBUS_PORT=502
ENV OPENPLC_WEBUI_PORT=8080
ENV OPENPLC_SCAN_CYCLE_MS=50

# Labels for versioning
LABEL org.sphere.openplc.version="${OPENPLC_VERSION}"
LABEL org.sphere.component="openplc-runtime"

ENTRYPOINT ["/entrypoint.sh"]
