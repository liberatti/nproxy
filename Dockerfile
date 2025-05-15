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
RUN rpmbuild -bb nproxy-openresty.spec

FROM --platform=${BUILDPLATFORM:-linux/amd64} node:lts AS frontend

WORKDIR /app
COPY web/package*.json .
RUN npm install && npm cache clean --force

COPY web web
COPY *.json .
RUN cd web && npm run build

FROM --platform=${BUILDPLATFORM:-linux/amd64} rockylinux:9-minimal AS main

ENV INSTALL_TYPE CONTAINER

ENV PATH ${PATH}:/opt/nproxy/.local/bin:/opt/nproxy/nginx/sbin
ENV LUA_PATH "/opt/nproxy/lualib/share/lua/5.4/?.lua;/opt/nproxy/lualib/share/lua/5.4/resty/?.lua;;"
ENV LUA_CPATH "/opt/nproxy/lualib/lib64/lua/5.4/?.so;/opt/nproxy/lualib/lib/?.so;/opt/nproxy/lualib/?.so;;"
ENV PYTHONUSERBASE /opt/nproxy/admin/site-packages

RUN microdnf install -y procps openssl bind-utils shadow-utils util-linux gcc-c++ \
    libX11 libXext libXi libXrender libXtst freetype sudo \
    python3.12 python3.12-devel python3.12-pip yajl lua wget\
  && microdnf update -y\
  && microdnf clean all\
  && python3.12 -m pip install --upgrade pip\
  && python3.12 -m pip install --upgrade setuptools

COPY --from=engine /root/rpmbuild/RPMS/**/*.rpm /RPMS/
RUN rpm -ivh /RPMS/*.rpm && rm -rf /RPMS

COPY --from=frontend /app/web/dist /opt/nproxy/admin/static
COPY --from=frontend /app/web/dist/index.html /opt/nproxy/admin/templates/

WORKDIR /opt/nproxy/admin

COPY api/requirements.txt /opt/nproxy/admin/
RUN pip3.12 install -r /opt/nproxy/admin/requirements.txt

COPY api /opt/nproxy/admin
COPY config /opt/nproxy/admin/config
COPY web/assets/swagger-ui /opt/nproxy/admin/static/swagger-ui
COPY openapi.yml /opt/nproxy/admin/static/swagger-ui/

RUN mkdir -p /opt/nproxy/lualib/share/lua/5.4/nproxy/
COPY lualib /opt/nproxy/lualib/share/lua/5.4/nproxy/

RUN chown -R nproxy /opt/nproxy

USER nproxy

EXPOSE 5000
EXPOSE 80
EXPOSE 443

ENTRYPOINT ["gunicorn", "-k", "eventlet", "-w", "1", "main:app", "-b", "0.0.0.0:5000"]
