Name:       mkdevnodes
Summary:    Fast MAKEDEV replacement
Version:    0.2
Release:    1
Group:      Applications/System
License:    GPLv2
Source0:    %{name}-%{version}.tgz

%description
A replacement for MAKEDEV. Instead of parsing hard-coded text files, mkdevnodes uses the information provided in sysfs to generate device nodes with mknod() as needed, as well as a few base device nodes that always need to be present. Mkdevnodes is thus extremely fast, as it doesn not need to read and/or parse text files from the root filesystem.

%files
