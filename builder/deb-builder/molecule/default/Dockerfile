# Debian 9.5
FROM debian@sha256:f1f61086ea01a72b30c7287adee8c929e569853de03b7c462a8ac75e0d0224c4
# additional meta-data makes it easier to clean up, find
LABEL org="Freedom of the Press"
LABEL image_name="debian-stretch-builder"

RUN apt-get -y update && apt-get upgrade -y && apt-get install -y \
        build-essential \
        debhelper \
        python \
        git \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*
