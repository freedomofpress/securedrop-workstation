FROM fedora:38
LABEL org="Freedom of the Press"
LABEL image_name="securedrop-workstation-qubes-4.2"

ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

RUN dnf install -y make

COPY Makefile Makefile

RUN make install-deps

COPY requirements requirements
RUN pip3 install --no-deps --require-hashes -r requirements/dev-requirements.txt

RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi
