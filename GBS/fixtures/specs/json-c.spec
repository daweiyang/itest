Name:		json-c
Version:	0.9
Release:	1
Summary:	A JSON implementation in C
Group:		Development/Libraries
License:	MIT
URL:		http://oss.metaparadigm.com/json-c/
Source0:	http://oss.metaparadigm.com/json-c/json-c-%{version}.tar.lzma

%description
JSON-C implements a reference counting object model that allows you to easily
construct JSON objects in C, output them as JSON formatted strings and parse
JSON formatted strings back into the C representation of JSON objects.

%package devel
Summary:	Development headers and library for json-c
Group:		Development/Libraries
Requires:	%{name} = %{version}-%{release}
Requires:	pkgconfig

%description devel
This package contains the development headers and library for json-c.

%files

%files devel
