%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
Name:       itest
Summary:    gbs system test automatic script and test cases
Version:    1.1
Release:    1
Group:      Development/Tools
License:    GPLv2
BuildArch:  noarch
URL:        http://www.tizen.org
Source0:    %{name}_%{version}.tar.gz
Requires:   python >= 2.7
Requires:   pexpect
BuildRequires:  python-devel

%description
gbs system test

%prep
%setup -q -n %{name}-%{version}

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=$RPM_BUILD_ROOT --prefix=%{_prefix}

%files
%defattr(-,root,root,-)
%{python_sitelib}/*
%{_bindir}/runtest
