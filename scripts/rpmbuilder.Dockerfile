ARG RPM_HASH
FROM quay.io/freedomofpress/rpmbuilder@sha256:${RPM_HASH}

LABEL MAINTAINER="Freedom of the Press Foundation"
LABEL APP="Localized RPM builder"
ARG USERID

USER root
RUN getent passwd $USERID > /dev/null || \
        ( usermod -u ${USERID} user && chown -R user: /home/user )

USER user
WORKDIR /sd
