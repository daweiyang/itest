Name:       xorg-x11-filesystem
Summary:    X.Org X11 filesystem layout
Version:    7.3
Release:    1
Group:      System/Base
License:    MIT
BuildArch:  noarch
URL:        http://www.redhat.com
Requires:   filesystem
Requires(pre): filesystem



%description
This package provides some directories which are required by other
packages which comprise the modularized X.Org X11R7 X Window System
release.  This package must be installed during OS installation
or upgrade, in order to force the creation of these directories,
and replace any legacy symbolic links that might be present in old
locations, which could result in upgrade failures.




%prep

%build



%install
rm -rf %{buildroot}

# NOTE: Do not replace these with _libdir or _includedir macros, they are
#       intentionally explicit.
mkdir -p "$RPM_BUILD_ROOT/usr/lib/X11"
mkdir -p "$RPM_BUILD_ROOT/usr/include/X11"

# whereas this is not
mkdir -p "$RPM_BUILD_ROOT%{_datadir}/X11"

mkdir -p "$RPM_BUILD_ROOT%{_bindir}"

UPGRADE_CMD="%{_bindir}/xorg-x11-filesystem-upgrade"

# NOTE: The quoted 'EOF' is required to disable variable interpolation
cat > "$RPM_BUILD_ROOT/${UPGRADE_CMD}" <<'EOF'
#!/bin/bash
#
# Modular X.Org X11R7 filesystem upgrade script.
#
# If any of the following dirs are symlinks, remove them and create a dir
# in its place.  This is required, so that modular X packages get installed
# into a real directory, and do not follow old compatibility symlinks
# provided in previous releases of the operating system.
#
# NOTE: Do not replace these with _libdir or _includedir macros, they are
#       intentionally explicit.
for dir in /usr/include/X11 /usr/lib/X11 ; do
[ -L "$dir" ] && rm -f -- "$dir" &> /dev/null
done
for dir in /usr/include/X11 /usr/lib/X11 ; do
[ ! -d "$dir" ] && mkdir -p "$dir" &> /dev/null
done
exit 0
EOF

chmod 0755 "$RPM_BUILD_ROOT/${UPGRADE_CMD}"



%pre
# NOTE: Do not replace these with _libdir or _includedir macros, they are
#       intentionally explicit.
# Remove old symlinks if present, and replace them with directories.
for dir in /usr/include/X11 /usr/lib/X11 ; do
[ -L "$dir" ] && rm -f -- "$dir" &> /dev/null
done
for dir in /usr/include/X11 /usr/lib/X11 ; do
[ ! -d "$dir" ] && mkdir -p "$dir" &> /dev/null
done
exit 0





%files
%defattr(-,root,root,-)
# NOTE: These are explicitly listed intentionally, instead of using rpm
#       macros, as these exact locations are required for compatibility
#       regardless of what _libdir or _includedir point to.
%dir /usr/lib/X11
%dir /usr/include/X11
%dir %{_datadir}/X11
%{_bindir}/xorg-x11-filesystem-upgrade


