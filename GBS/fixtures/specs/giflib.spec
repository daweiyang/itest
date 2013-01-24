Summary: Library for manipulating GIF format image files
Name: giflib
Version: 4.1.6
Release: 9
License: MIT
URL: http://sourceforge.net/projects/giflib/
Source0: http://downloads.sourceforge.net/giflib/%{name}-%{version}.tar.gz
 
Group: System/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: pkgconfig(x11)
BuildRequires: pkgconfig(ice)
BuildRequires: pkgconfig(sm)
BuildRequires: pkgconfig(xv)

Obsoletes: libungif <= %{version}-%{release}
Provides: libungif <= %{version}-%{release}

%description
The giflib package contains a shared library of functions for
loading and saving GIF format image files.  It is API and ABI compatible
with libungif, the library which supported uncompressed GIFs while the
Unisys LZW patent was in effect.

Install the giflib package if you need to write programs that use GIF files.
You should also install the giflib-utils package if you need some simple
utilities to manipulate GIFs.

%package devel
Summary: Development tools for programs which will use the libungif library
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Provides: libungif-devel <= %{version}-%{release}
Obsoletes: libungif-devel <= %{version}-%{release}

%description devel
This package contains the static libraries, header files and
documentation necessary for development of programs that will use the
giflib library to load and save GIF format image files.

You should install this package if you need to develop programs which
will use giflib library functions.  You'll also need to install the
giflib package.

%package utils
Summary: Programs for manipulating GIF format image files
Group: Applications/Multimedia
Requires: %{name} = %{version}-%{release}
Obsoletes: libungif-progs <= %{version}-%{release}

%description utils
The giflib-utils package contains various programs for manipulating
GIF format image files.

Install this package if you need to manipulate GIF format image files.
You'll also need to install the giflib package.

%files 

%files devel

%files utils
