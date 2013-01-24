#!/bin/bash
# Clean up the tmp files, user, installed files, etc in the test machines
# after running test
# This script will be automatically executed by Jenkins

if [[ $USER != root ]]; then
    echo "Root privileges are required for this script"
    exit 1
fi

# Clean up temporary user when running gbs_export_multi_users_run_export.case
# the temporary user name prefix is user

tmp_users=$(compgen -u itestuser)
if [ -n "$tmp_users" ]; then
    for _user in $tmp_users
    do
        echo "Delete user: ${_user}"
        /usr/sbin/userdel -rf ${_user}
    done
fi
rm -rf /var/tmp/itestuser*

# Remove /etc/bash_completion.d/gbs.bash installed by itest
# gbs tab completion will be supported by gbs 0.13
rm -f /etc/bash_completion.d/gbs.bash

# Clean up itest installed from source code using python setup.py install
# We'll install itest from repo later

rm -rf /usr/share/itest

if python -c "import itest; print itest.__file__" >/dev/null 2>&1; then
    install_dir=$(dirname $(python -c "import itest; print itest.__file__"))
    rm -rf $install_dir
    if which runtest; then
        rm -f $(which runtest)
    fi
fi

echo Done
