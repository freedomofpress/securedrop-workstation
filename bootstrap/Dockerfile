FROM registry.fedoraproject.org/fedora:32
LABEL org="Freedom of the Press"
LABEL image_name="securedrop-workstation-qubes-4.1"

ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN dnf install -y make

COPY Makefile Makefile

RUN make install-deps

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi
