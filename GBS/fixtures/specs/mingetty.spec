#specfile originally created for Fedora, modified for Moblin Linux
Summary: A compact getty program for virtual consoles only
Name: mingetty
Version: 1.08
License: GPLv2+
Release: 3.9
Group: System/Base
URL: http://sourceforge.net/projects/mingetty/
Source: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz
Patch: mingetty-1.00-opt.patch
BuildRoot: %{_tmppath}/%{name}-root

%description
The mingetty program is a lightweight, minimalist getty program for
use only on virtual consoles.  Mingetty is not suitable for serial
lines (you should use the mgetty program in that case).

%prep
%setup -q
%patch -p0

%files
