FROM --platform=${BUILDPLATFORM:-linux/amd64} rockylinux:9 AS engine

ENV MODSECURITY_INC "/opt/nproxy/modsec/include"
ENV MODSECURITY_LIB "/opt/nproxy/modsec/lib"

RUN dnf -y install 'dnf-command(config-manager)' \
  && dnf config-manager --set-enabled devel \
  && dnf -y install \
    git wget openssl-devel gcc gcc-c++ zlib-devel make automake libtool readline-devel \
    libinput libcurl-devel pcre2-devel libxml2-devel libxslt-devel libgcrypt-devel gd-devel \
    libffi-devel rpmdevtools rpm-build rpm-devel yajl-devel lua-devel python3.12 python3.12-devel \
    yajl lua perl-ExtUtils-Embed shadow-utils util-linux python3.12-pip openldap-devel \
  && dnf clean all

WORKDIR /root/rpmbuild/SPECS
COPY packages/ssdeep.spec .
RUN rpmbuild -bb ssdeep.spec \
  && rpm -ivh /root/rpmbuild/RPMS/**/ssdeep-*.rpm

RUN wget https://dl.fedoraproject.org/pub/epel/9/Everything/x86_64/Packages/l/luarocks-3.9.2-5.el9.noarch.rpm \
  && rpm -ivh luarocks-3.9.2-5.el9.noarch.rpm \
  && rm -f luarocks-3.9.2-5.el9.noarch.rpm

COPY packages/nproxy-openresty.spec /root/rpmbuild/SPECS/
#RUN rpmbuild -bb nproxy-openresty.spec