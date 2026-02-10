ARG FEDORA_VERSION=37
FROM quay.io/fedora/fedora:${FEDORA_VERSION}

# Install "make" so that we can run the makefile targets for dev deps.
RUN dnf install -y make && dnf clean all -y

WORKDIR /app
COPY Makefile Makefile
COPY rpm-build/SPECS rpm-build/SPECS

ARG DEPS=build-deps
RUN make ${DEPS} && dnf clean all -y

# Cleanup
RUN rm -rf rpm-build

# Permit user customization, for unknown platforms
ARG USER_NAME=root
ARG USER_ID=0
RUN if test $USER_NAME != root ; then \
      useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME \
      && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; \
    fi
