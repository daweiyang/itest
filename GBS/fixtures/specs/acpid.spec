Name:           acpid
Version:        2.0.14
Release:        1
License:        GPLv2+ and BSD
Summary:        ACPI Event Daemon
Group:          System/Daemons
Source:         %{name}-%{version}.zip
Source2:        acpid.video.conf
Source3:        acpid.power.conf
Source4:        acpid.power.sh
Source5:        acpid.lid.conf
Source6:        acpid.lid.sh
Source7:        acpid.battery.sh
Source8:        acpid.battery.conf
Source9:        acpid.ac.conf
Source13:       acpid-start-script
Source14:       acpid.start.sh
Source15:       acpid.service
Source16:       acpid
Patch1:         acpid-2.0.9-makefile.patch

Url:            http://tedfelix.com/linux/acpid-netlink.html
ExclusiveArch: ia64 x86_64 %{ix86}

%description
acpid is a daemon that dispatches ACPI events to user-space programs.

%package extra-docs
Summary:        sample docs and sample scripts for apcid
Group:          Documentation
Requires:       %{name} = %{version}

%description extra-docs
Extra sample docs and scripts for acpid.

%files

%files extra-docs
