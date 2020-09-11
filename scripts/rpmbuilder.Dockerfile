ARG CONTAINER_HASH
FROM fedora@sha256:${CONTAINER_HASH}
LABEL MAINTAINER="Freedom of the Press Foundation"
LABEL DESCRIPTION="RedHat tooling for building RPMs for Fedora"
ARG USERID
ARG FEDORA_PKGR_VER

RUN echo "${FEDORA_PKGR_VER}"

RUN dnf update -y && \
    dnf install -y \
    fedora-packager-${FEDORA_PKGR_VER}.noarch \
    make \
    python3-cryptography \
    python3-devel \
    python3-requests \
    python3-setuptools \
    vim && \
    yum clean all

ENV HOME /home/user
RUN useradd --create-home --home-dir $HOME user \
    && chown -R user:user $HOME && \
    su -c rpmdev-setuptree user

RUN getent passwd $USERID > /dev/null || \
        ( usermod -u ${USERID} user && chown -R user: /home/user )

USER user

WORKDIR $HOME/rpmbuild
VOLUME $HOME/rpmbuild

CMD ["/usr/bin/bash"]
WORKDIR /sd
