Name:		nproxy-openresty
Version:	1.0
Release:	alpha%{?dist}
Summary:	NProxy engine powered by openresty

License:	Apache-2.0
Source0:	%{name}-%{version}.tar.gz    

BuildRequires: openldap-devel luarocks wget openssl-devel gcc gcc-c++ zlib-devel openssl-devel make automake libtool readline-devel libinput libcurl-devel pcre2-devel libxml2-devel libxslt-devel libgcrypt-devel gd-devel perl-ExtUtils-Embed 
Requires: bash, lua, ssdeep = 2.14.1, shadow-utils, util-linux, wget, gcc, sudo

%undefine __brp_mangle_shebangs 

%description
%prep

cd /root/rpmbuild/BUILD

if [[ ! -e  openresty-1.27.1.1.tar.gz ]];then
	wget https://openresty.org/download/openresty-1.27.1.1.tar.gz
	tar -xf openresty-1.27.1.1.tar.gz
	install -d openresty-1.27.1.1/modules
fi

if [[ ! -e modsecurity-v3.0.12.tar.gz ]];then
	wget https://github.com/SpiderLabs/ModSecurity/releases/download/v3.0.12/modsecurity-v3.0.12.tar.gz 
	tar -xf modsecurity-v3.0.12.tar.gz 
fi

if [[ ! -e modsecurity-nginx-v1.0.3.tar.gz ]];then
	wget https://github.com/SpiderLabs/ModSecurity-nginx/releases/download/v1.0.3/modsecurity-nginx-v1.0.3.tar.gz
	tar -xf modsecurity-nginx-v1.0.3.tar.gz
	mv modsecurity-nginx-v1.0.3 openresty-1.27.1.1/modules/
fi

if [[ ! -e 1.2.6.tar.gz ]];then
	wget https://github.com/liberatti/nginx-sticky-module-ng/archive/refs/tags/1.2.6.tar.gz
	tar -xf 1.2.6.tar.gz
	mv nginx-sticky-module-ng-1.2.6 openresty-1.27.1.1/modules/
fi

if [[ ! -e 0.4.1.tar.gz ]];then
	wget https://github.com/liberatti/nginx_upstream_check_module/archive/refs/tags/0.4.1.tar.gz
	tar -xf 0.4.1.tar.gz
	mv nginx_upstream_check_module-0.4.1 openresty-1.27.1.1/modules/
fi

if [[ ! -e v1.0.0.tar.gz ]];then
	wget https://github.com/liberatti/nginx_ajp_module/archive/refs/tags/v1.0.0.tar.gz
	tar -xf v1.0.0.tar.gz
	mv nginx_ajp_module-1.0.0 openresty-1.27.1.1/modules/
fi
if [[ ! -e lua-5.1.5.tar.gz ]];then
	wget https://www.lua.org/ftp/lua-5.1.5.tar.gz
	tar -xf lua-5.1.5.tar.gz
fi

%build
cd /root/rpmbuild/BUILD/lua-5.1.5
make -j$(nproc) linux

cd /root/rpmbuild/BUILD/modsecurity-v3.0.12
./configure --prefix=/opt/nproxy/modsec --with-yajl --with-pcre2 --with-ssdeep --with-lua
make -j 4
make install

cd /root/rpmbuild/BUILD/openresty-1.27.1.1
./configure --with-compat --with-http_ssl_module --with-http_stub_status_module\
	--with-http_v2_module\
	--without-lua_redis_parser\
	--without-lua_resty_redis\
	--without-lua_resty_mysql\
	--with-debug\
	--with-cc-opt='-D FD_SETSIZE=32768'\
    --add-dynamic-module=modules/nginx_ajp_module-1.0.0\
    --add-module=modules/nginx_upstream_check_module-0.4.1\
    --add-dynamic-module=modules/nginx-sticky-module-ng-1.2.6\
    --add-dynamic-module=modules/modsecurity-nginx-v1.0.3\
    --prefix=/opt/nproxy
make -j 4

%install
install -d %{buildroot}/opt/nproxy/html
install -d %{buildroot}/opt/nproxy/logs
install -d %{buildroot}/opt/nproxy/run
install -d %{buildroot}/opt/nproxy/cache
install -d %{buildroot}/opt/nproxy/data

install -d %{buildroot}/opt/nproxy/nginx/conf
install -d %{buildroot}/opt/nproxy/nginx/sbin
install -d %{buildroot}/opt/nproxy/nginx/modules

install -d %{buildroot}/opt/nproxy/luajit/bin
install -d %{buildroot}/opt/nproxy/luajit/lib
install -d %{buildroot}/opt/nproxy/luajit/include/luajit-2.1
install -d %{buildroot}/opt/nproxy/luajit/share/luajit-2.1/jit
install -d %{buildroot}/opt/nproxy/luajit/share/lua/5.1
install -d %{buildroot}/opt/nproxy/luajit/lib/lua/5.1
install -d %{buildroot}/opt/nproxy/lualib/cjson

install -d %{buildroot}/opt/nproxy/luajit/include/lua-5.1

cd /root/rpmbuild/BUILD/lua-5.1.5/src
install -p -m 0755 lua luac %{buildroot}/opt/nproxy/luajit/bin
install -p -m 0644 lua.h luaconf.h lualib.h lauxlib.h ../etc/lua.hpp %{buildroot}/opt/nproxy/luajit/include/lua-5.1
install -p -m 0644 liblua.a %{buildroot}/opt/nproxy/luajit/lib/lua/5.1

install /root/rpmbuild/BUILD/openresty-1.27.1.1/COPYRIGHT %{buildroot}/opt/nproxy/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/LuaJIT-2.1-20240815/src
install -m 0755 luajit %{buildroot}/opt/nproxy/luajit/bin/luajit-2.1.ROLLING
install -m 0644 libluajit.a %{buildroot}/opt/nproxy/luajit/lib/libluajit-5.1.a || :
install -m 0755 libluajit.so %{buildroot}/opt/nproxy/luajit/lib/libluajit-5.1.so.2.1.ROLLING
install -m 0644 lua.h lualib.h lauxlib.h luaconf.h lua.hpp luajit.h  %{buildroot}/opt/nproxy/luajit/include/luajit-2.1

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/LuaJIT-2.1-20240815/src/jit
install -m 0644 bc.lua bcsave.lua dump.lua p.lua v.lua zone.lua dis_x86.lua dis_x64.lua dis_arm.lua dis_arm64.lua dis_arm64be.lua dis_ppc.lua dis_mips.lua dis_mipsel.lua dis_mips64.lua dis_mips64el.lua dis_mips64r6.lua dis_mips64r6el.lua vmdef.lua %{buildroot}/opt/nproxy/luajit/share/luajit-2.1/jit

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-cjson-2.1.0.14
install -m 0644 cjson.so %{buildroot}/opt/nproxy/lualib/cjson.so
install -m 0644 lua/*.lua %{buildroot}/opt/nproxy/lualib/
install -m 0644 lua/cjson/*.lua %{buildroot}/opt/nproxy/lualib/cjson/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-signal-0.04
install -d %{buildroot}/opt/nproxy/lualib/resty
install lib/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty
install librestysignal.so %{buildroot}/opt/nproxy/lualib/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-rds-parser-0.06
install -d %{buildroot}/opt/nproxy/lualib/rds
install parser.so %{buildroot}/opt/nproxy/lualib/rds

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-dns-0.23
install -d %{buildroot}/opt/nproxy/lualib/resty/dns/
install lib/resty/dns/*.lua %{buildroot}/opt/nproxy/lualib/resty/dns/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-memcached-0.17
install -d %{buildroot}/opt/nproxy/lualib/resty
install lib/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-string-0.16
install -d %{buildroot}/opt/nproxy/lualib/resty
install lib/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-upload-0.11
install -d %{buildroot}/opt/nproxy/lualib/resty
install lib/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-websocket-0.12
install -d %{buildroot}/opt/nproxy/lualib/resty/websocket
install lib/resty/websocket/*.lua %{buildroot}/opt/nproxy/lualib/resty/websocket/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-lock-0.09
install -d %{buildroot}/opt/nproxy/lualib/resty/
install lib/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-lrucache-0.15
install -d %{buildroot}/opt/nproxy/lualib/resty/lrucache
install lib/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty/
install lib/resty/lrucache/*.lua %{buildroot}/opt/nproxy/lualib/resty/lrucache/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-core-0.1.30
install -d %{buildroot}/opt/nproxy/lualib/resty/core/
install -d %{buildroot}/opt/nproxy/lualib/ngx/
install -d %{buildroot}/opt/nproxy/lualib/ngx/ssl
install lib/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty/
install lib/resty/core/*.lua %{buildroot}/opt/nproxy/lualib/resty/core/
install lib/ngx/*.lua %{buildroot}/opt/nproxy/lualib/ngx/
install lib/ngx/ssl/*.lua %{buildroot}/opt/nproxy/lualib/ngx/ssl/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-upstream-healthcheck-0.08
install -d %{buildroot}/opt/nproxy/lualib/resty/upstream/
install lib/resty/upstream/*.lua %{buildroot}/opt/nproxy/lualib/resty/upstream/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-limit-traffic-0.09
install -d %{buildroot}/opt/nproxy/lualib/resty/limit/
install lib/resty/limit/*.lua %{buildroot}/opt/nproxy/lualib/resty/limit/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-shell-0.03
install -d %{buildroot}/opt/nproxy/lualib/resty/
install lib/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-tablepool-0.03
install lib/*.lua %{buildroot}/opt/nproxy/lualib/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/opm-0.0.8
install -d %{buildroot}/opt/nproxy/bin
install bin/* %{buildroot}/opt/nproxy/bin/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/resty-cli-0.30
install bin/* %{buildroot}/opt/nproxy/bin/

cp /root/rpmbuild/BUILD/openresty-1.27.1.1/build/resty.index  %{buildroot}/opt/nproxy/
cp -r /root/rpmbuild/BUILD/openresty-1.27.1.1/build/pod %{buildroot}/opt/nproxy/

#export LUA_INCDIR=/root/rpmbuild/BUILD/openresty-1.27.1.1/LuaJIT-2.1-20240815/src/
luarocks config lua_dir %{buildroot}/opt/nproxy/luajit
luarocks install --tree=/root/rpmbuild/BUILD/lualib lualdap --lua-version=5.1

luarocks install --tree=/root/rpmbuild/BUILD/lualib base64 --lua-version=5.1
install /root/rpmbuild/BUILD/lualib/share/lua/5.1/*.lua %{buildroot}/opt/nproxy/lualib/

luarocks install --tree=/root/rpmbuild/BUILD/lualib lua-resty-http --lua-version=5.1

luarocks install --tree=/root/rpmbuild/BUILD/lualib lua-resty-jwt --lua-version=5.1
install /root/rpmbuild/BUILD/lualib/share/lua/5.1/resty/*.lua %{buildroot}/opt/nproxy/lualib/resty
install -d %{buildroot}/opt/nproxy/lualib/resty/openssl/x509/extension
install /root/rpmbuild/BUILD/lualib/share/lua/5.1/resty/openssl/*.lua %{buildroot}/opt/nproxy/lualib/resty/openssl
install /root/rpmbuild/BUILD/lualib/share/lua/5.1/resty/openssl/x509/*.lua %{buildroot}/opt/nproxy/lualib/resty/openssl/x509
install /root/rpmbuild/BUILD/lualib/share/lua/5.1/resty/openssl/x509/extension/*.lua %{buildroot}/opt/nproxy/lualib/resty/openssl/x509/extension

install /root/rpmbuild/BUILD/lualib/lib64/lua/5.1/* %{buildroot}/opt/nproxy/lualib/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/nginx-1.27.1
install -c objs/nginx %{buildroot}/opt/nproxy/nginx/sbin/nginx
install -c conf/* %{buildroot}/opt/nproxy/nginx/conf
install -c objs/*_module.so %{buildroot}/opt/nproxy/nginx/modules/

cd /root/rpmbuild/BUILD/modsecurity-v3.0.12
install -d %{buildroot}/opt/nproxy/modsec/bin
install -d %{buildroot}/opt/nproxy/modsec/conf
install -d %{buildroot}/opt/nproxy/modsec/lib/pkgconfig
install -d %{buildroot}/opt/nproxy/modsec/include/modsecurity/actions
install -d %{buildroot}/opt/nproxy/modsec/include/modsecurity/collection

install -c tools/rules-check/modsec-rules-check %{buildroot}/opt/nproxy/modsec/bin/modsec-rules-check
install -c src/.libs/* %{buildroot}/opt/nproxy/modsec/lib/
install -c -m 644 headers/modsecurity/actions/*.h %{buildroot}/opt/nproxy/modsec/include/modsecurity/actions/
install -c -m 644 headers/modsecurity/collection/*.h %{buildroot}/opt/nproxy/modsec/include/modsecurity/collection/
install -c -m 644 headers/modsecurity/*.h %{buildroot}/opt/nproxy/modsec/include/modsecurity/
install -c -m 644 examples/reading_logs_via_rule_message/reading_logs_via_rule_message.h %{buildroot}/opt/nproxy/modsec/include/modsecurity/
install -c -m 644 modsecurity.pc %{buildroot}/opt/nproxy/modsec/lib/pkgconfig/

%files
%attr(0744, root, root) /opt/nproxy/modsec
%attr(0744, root, root) /opt/nproxy/bin
%attr(0744, root, root) /opt/nproxy/luajit
%attr(0744, root, root) /opt/nproxy/lualib
%attr(0744, root, root) /opt/nproxy/nginx
%attr(0744, root, root) /opt/nproxy/pod
%attr(0744, root, root) /opt/nproxy/resty.index
%attr(0744, root, root) /opt/nproxy/COPYRIGHT
%attr(0744, root, root) /opt/nproxy/html
%attr(0744, root, root) /opt/nproxy/logs
%attr(0744, root, root) /opt/nproxy/run
%attr(0744, root, root) /opt/nproxy/cache

%post
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/sbin"

rm -f /opt/nproxy/modsec/lib/libmodsecurity.so.3 /opt/nproxy/modsec/lib/libmodsecurity.so
ln -s /opt/nproxy/modsec/lib/libmodsecurity.so.3.0.12 /opt/nproxy/modsec/lib/libmodsecurity.so.3
ln -s /opt/nproxy/modsec/lib/libmodsecurity.so.3.0.12 /opt/nproxy/modsec/lib/libmodsecurity.so
ln -s /opt/nproxy/logs /opt/nproxy/nginx/logs
ldconfig -n /opt/nproxy/modsec/lib

cd /opt/nproxy/luajit/lib
ln -sf libluajit-5.1.so.2.1.ROLLING /opt/nproxy/luajit/lib/libluajit-5.1.so && \
ln -sf libluajit-5.1.so.2.1.ROLLING /opt/nproxy/luajit/lib/libluajit-5.1.so.2 || :
ln -sf luajit-2.1.ROLLING /opt/nproxy/luajit/bin/luajit
ldconfig -n 2>/dev/null /opt/nproxy/luajit/lib

if [ `grep -c nproxy /etc/passwd` = "0" ]; then
	useradd -r -d /opt/nproxy -s /bin/false nproxy
	echo 'nproxy ALL=(ALL:ALL) NOPASSWD: ALL' > /etc/sudoers.d/nproxy
fi
chown -R nproxy:nproxy /opt/nproxy

%changelog
* Thu Feb 04 2025 Gustavo Liberatti
- Create nproxy openresty with modsecurity 3x
