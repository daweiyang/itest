%define release_name Tizen
%define dist_version 1.2.0.90

Summary:	Tizen release files
Name:		tizen-release
Version:	1.2.0.90
Release:	1
License:	GPLv2
Group:		System/Base
URL:		http://www.tizen.com
Provides:	system-release = %{version}-%{release}
BuildArch:	noarch
%description
Tizen release files such as various /etc/ files that define the release.

%prep

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/etc
echo "Tizen release %{dist_version} (%{release_name})" > $RPM_BUILD_ROOT/etc/tizen-release

ln -s tizen-release $RPM_BUILD_ROOT/etc/system-release


%clean
rm -rf $RPM_BUILD_ROOT

%files
%config %attr(0644,root,root) /etc/tizen-release
/etc/system-release

