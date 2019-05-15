# fedora:29 2019-04-15
FROM fedora@sha256:8ee55e140e8751492ab2cfa4513c82093cd2716df9311ea6f442f1f1259cbb3e
LABEL maintainer="Freedom of the Press Foundation"
RUN dnf update -y && \
    dnf install -y \
    createrepo_c

COPY sd-workstation/apt-test-pubkey.asc /tmp/apt-test-pubkey.asc
RUN rpm --import /tmp/apt-test-pubkey.asc

RUN mkdir /repo
WORKDIR /repo
