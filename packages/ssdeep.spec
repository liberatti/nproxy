Name:           ssdeep
Version:        2.14.1
Release:        1%{?dist}
Summary:        Fuzzy hashing API and fuzzy hashing tool   

License:       GPL-2.0 license
Source0:       %{name}-%{version}.tar.gz    

BuildRequires: wget openssl-devel gcc gcc-c++ zlib-devel openssl-devel make automake libtool readline-devel libinput libcurl-devel pcre2-devel libxml2-devel libxslt-devel libgcrypt-devel gd-devel perl-ExtUtils-Embed 
Requires:bash

%description
%prep
cd /root/rpmbuild/BUILD
rm -Rf ssdeep

wget https://github.com/ssdeep-project/ssdeep/archive/refs/tags/release-2.14.1.tar.gz
tar -xf release-2.14.1.tar.gz

%build
cd /root/rpmbuild/BUILD/ssdeep-release-2.14.1
./bootstrap
./configure
make -j 4

%install
mkdir -p %{buildroot}/usr/local/bin
mkdir -p %{buildroot}/usr/local/lib
mkdir -p %{buildroot}/usr/local/include
mkdir -p %{buildroot}/usr/local/share/man/man1

cd /root/rpmbuild/BUILD/ssdeep-release-2.14.1
install -c .libs/libfuzzy.so.2.1.0 %{buildroot}/usr/local/lib/libfuzzy.so.2.1.0
install -c .libs/libfuzzy.lai %{buildroot}/usr/local/lib/libfuzzy.la
install -c .libs/libfuzzy.a %{buildroot}/usr/local/lib/libfuzzy.a
install -c ssdeep %{buildroot}/usr/local/bin
install -c -m 644 fuzzy.h edit_dist.h %{buildroot}/usr/local/include/
install -c -m 644 ssdeep.1 %{buildroot}/usr/local/share/man/man1/

%files
%attr(0744, root, root) /usr/local/bin/*
%attr(0744, root, root) /usr/local/lib/*
%attr(0744, root, root) /usr/local/include/*
%attr(0744, root, root) /usr/local/share/man/man1/*

%post
ln -s -f /usr/local/lib/libfuzzy.so.2.1.0 /usr/local/lib/libfuzzy.so.2
ln -s -f /usr/local/lib/libfuzzy.so.2.1.0 /usr/local/lib/libfuzzy.so
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/sbin" 
ldconfig -n /usr/local/lib

%changelog
* Sat Aug 19 2023 Gustavo Liberatti
- Create