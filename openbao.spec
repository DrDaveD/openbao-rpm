# Forked from vault.spec by John Boero - jboero@hashicorp.com

Name: openbao
Version: 2.0.0-alpha20240329
Release: 1%{?dist}
Summary: Openbao is a tool for securely accessing secrets
License: MPL
Source0: https://github.com/opensciencegrid/%{name}-rpm/archive/v%{version}/%{name}-rpm-%{version}.tar.gz
# This is created by ./make-source-tarball
Source1: %{name}-src-%{version}.tar.gz

#BuildRequires: golang
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
URL: https://openbao.org

# This is to avoid
#   *** ERROR: No build ID note found
%define debug_package %{nil}

%description
Openbao secures, stores, and tightly controls access to tokens, passwords,
certificates, API keys, and other secrets in modern computing. Openbao handles
leasing, key revocation, key rolling, and auditing. Through a unified API, users
can access an encrypted Key/Value store and network encryption-as-a-service, or
generate AWS IAM/STS credentials, SQL/NoSQL databases, X.509 certificates, SSH
credentials, and more.

%prep
%setup -q -n %{name}-rpm-%{version}
RPMDIR=`pwd`
%setup -q -T -b 1 -n %{name}-src-%{version}

%build
# starts out in %{name}-src-%{version} directory
export GOPATH="`pwd`/gopath"
export PATH=$PWD/go/bin:$GOPATH/bin:$PATH
export GOPROXY=file://$(go env GOMODCACHE)/cache/download
cd %{name}-%{version}
# this prevents it from complaining that ui assets are too old
touch http/web_ui/index.html
# this prevents the build from trying to use git to figure out the version
#  which fails because there's no git info
ln -s /bin/true $GOPATH/bin/git
make dev-ui

%install
# starts out in %{name}-src-%{version} directory
mkdir -p %{buildroot}%{_bindir}/
cp -p %{name}-%{version}/bin/%{name} %{buildroot}%{_bindir}/

cd ../%{name}-rpm-%{version}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}.d
cp -p openbao.hcl %{buildroot}%{_sysconfdir}/%{name}.d

mkdir -p %{buildroot}%{_sharedstatedir}/%{name}

mkdir -p %{buildroot}/usr/lib/systemd/system/
cp -p openbao.service %{buildroot}/usr/lib/systemd/system/

%clean
export GOPATH="`pwd`/gopath"
export PATH=$PWD/go/bin:$GOPATH/bin:$PATH
go clean -modcache
rm -rf %{buildroot}
rm -rf %{_builddir}/%{name}-*-%{version}

%files
%verify(not caps) %{_bindir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}.d/%{name}.hcl
%attr(0750,%{name},%{name}) %dir %{_sharedstatedir}/%{name}
/usr/lib/systemd/system/%{name}.service

%pre
getent group %{name} > /dev/null || groupadd -r %{name}
getent passwd %{name} > /dev/null || \
    useradd -r -d %{_sharedstatedir}/%{name} -g %{name} \
    -s /sbin/nologin -c "openbao secret management tool" %{name}
exit 0

%post
/usr/bin/systemctl daemon-reload
%systemd_post %{name}.service
/sbin/setcap cap_ipc_lock=+ep %{_bindir}/%{name}

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%changelog
