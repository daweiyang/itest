#!/bin/bash
# vim: set sw=4 ts=4 ai et:
#set -x

_supported_distro="SuSE fedora ubuntu"
_http_proxy="http://proxy01.cd.intel.com:911"
_no_proxy=".intel.com"
_old_repo="http://download.tizen.org/tools"
_new_repo="http://download.otctools.jf.intel.com/Tools"
_repo_root=
_distro=""
_version=""
_modules="gbs depanneur osc build  qemu-arm-static git-buildpackage-rpm git-buildpackage-common \
          createrepo libyaml-perl pristine-tar"
_id=""
# upgrade.sh's options
opts="o n"
# miscs generated in the process
binfmt_miscs="alpha arm armeb m68k mips mipsel mips64 mips64el ppc sh4 sh4eb sparc s390x"


function usage()
{
    echo "Usage: `basename $0` [-h|-o|-n|-i] repo"
    echo
    echo "  -h"
    echo "          help message"
    echo "  -o"
    echo "          specify the old gbs version repo"
    echo "  -n"
    echo "          specify the new gbs version repo"
    echo "  -i"
    echo "          specify a repo to install gbs"
}

function set_proxy()
{
    if [ -f /etc/sysconfig/proxy ]; then
        sed -i 's%^PROXY_ENABLED="no"%PROXY_ENABLED="yes"%' /etc/sysconfig/proxy
        sed -i 's%^HTTP_PROXY=""%HTTP_PROXY="'${_http_proxy}'"%' /etc/sysconfig/proxy
        sed -i 's%^HTTPS_PROXY=""%HTTP_PROXY="'${_http_proxy}'"%' /etc/sysconfig/proxy
        sed -i 's%^NO_PROXY=".*"%NO_PROXY="localhost, 127.0.0.1, '${_no_proxy}'"%' /etc/sysconfig/proxy
    fi

    export http_proxy=${_http_proxy}
    export https_proxy=${_http_proxy}
    export no_proxy=.intel.com
}

function linux_distribution()
{
    # maybe not a unix system
    if [ ! -d /etc ]; then
        _distro=""
        _version=""
        _id=""
        return 1
    fi
    # identify debian-like system
    if [ -e /etc/lsb-release ]; then
        _distro=$(sed -n 's/DISTRIB_ID\s*=\s*\(.*\)/\1/p' /etc/lsb-release)
        _version=$(sed -n 's/DISTRIB_RELEASE\s*=\s*\(.*\)/\1/p' /etc/lsb-release)
        _id=$(sed -n 's/DISTRIB_CODENAME\s*=\s*\(.*\)/\1/p' /etc/lsb-release)
        return 0
    fi

    if [ -e /etc/SuSE-release ]
    then
        _distro=`cat /etc/SuSE-release|head -1|awk '{print $1}'`
        _version=`cat /etc/SuSE-release|head -1|awk '{print $2}'`
        return 0
    fi

    # detect xxx-release to get os info
    release_file=$(ls /etc | grep -E "(\w+)[-_](release|version)" | sort | head -1)
    if [ $? -ne 0 ]; then
        _distro="unknown"
        _version=""
        _id=""
        return 1
    fi

    _distro=$(echo $release_file | sed -n -r 's/(\w+)[-_](release|version)/\1/p')
    # check supported distro list
    echo ${_supported_distro} | grep -w "${_distro}" 2>&1 > /dev/null
    # if not supported
    if [ $? -ne 0 ]; then
        _distro="unknown"
        _version=""
        _id=""
        return 1
    fi
    # LSB format release file: distro release x.x (code)
    line=$(grep -E "(.+) release ([0-9.]+) [^(]*(\((.+)\))?" /etc/$release_file)
    if [ $? -eq 0 ]; then
        _distro=$(echo $line | sed -n -r 's/(.+) release ([0-9.]+) [^(]*(\((.+)\))?/\1/p')
        _version=$(echo $line | sed -n -r 's/(.+) release ([0-9.]+) [^(]*(\((.+)\))?/\2/p')
        _id=$(echo $line | sed -n -r 's/(.+) release ([0-9.]+) [^(]*(\((.+)\))?/\3/p' 2>/dev/null)
        return 0
    fi
    # Pre-LSB format release file: distro x.x (code)
    line=$(grep -E "([^0-9]+) (release )?([0-9.]+) [^(]*(\((.+)\))?" /etc/$release_file)
    if [ $? -eq 0 ]; then
        _distro=$(echo $line | sed -n -r 's/([^0-9]+) (release )?([0-9.]+) [^(]*(\((.+)\))?/\1/p')
        _version=$(echo $line | sed -n -r 's/([^0-9]+) (release )?([0-9.]+) [^(]*(\((.+)\))?/\3/p')
        _id=$(echo $line | sed -n -r 's/([^0-9]+) (release )?([0-9.]+) [^(]*(\((.+)\))?/\4/p' 2>/dev/null)
        return 0
    fi
    # other format
    line=$(head -1 /etc/$release_file)
    _version=$(echo $line | awk '{print $1}')
    _id=$(echo $line | awk '{print $2}')
    return 0
}

function urlwrapper()
{
    str="${_repo_root}/${_distro}_${_version}"
    echo $str
    return
}

function getmodules()
{
    if [ "${_distro}" == "Ubuntu" ]; then
        _modules="${_modules} libcrypt-ssleay-perl"
        echo ${_modules}
        return
    fi
    if [ "${_distro}" == "openSUSE" ]; then
        _modules="${_modules} build-mkdrpms perl-Crypt-SSLeay"
        echo ${_modules}
        return
    fi

    _modules="${_modules} perl-Crypt-SSLeay"
    echo ${_modules}
}

function repo_update()
{
    echo "Update repositories..."
    # Ubuntu repo updates
    if [ "${_distro}" == "Ubuntu" ]
    then
        if [ -f /var/lib/apt/lists/lock ]
        then
            rm -f /var/lib/apt/lists/lock
        fi

        if grep -E "(tizen\.org|otctools\.jf\.intel\.com)" /etc/apt/sources.list >/dev/null
        then
            sed -i -r 's%^deb http.*(tizen\.org|otctools\.jf\.intel\.com).*$%deb '$(urlwrapper)' \/%' /etc/apt/sources.list
        else
            echo "deb $(urlwrapper) /" >> /etc/apt/sources.list
        fi

        apt-get -qq update
    # fedora repo updates
    elif [ "${_distro}" == "Fedora" ]
    then
        killall -q -9 yum
        killall -q -9 packagekitd

        repos=$(grep -E "(tizen\.org|otctools\.jf\.intel\.com)" /etc/yum.repos.d/*.repo|awk -F: '{print $1}')
        # delete old repos
        for _repo in $repos
        do
            mv ${_repo} ${_repo}.backup 2>&1 >/dev/null
        done

        # set repo
        if ! rpm -q yum-config-manager >/dev/null
        then
            yum -y install --nogpgcheck yum-utils >/dev/null
        fi
        yum-config-manager --add-repo=$(urlwrapper)
        yum clean all
        yum -y makecache
    # opensuse repo updates
    elif [ "${_distro}" == "openSUSE" ]
    then
        killall -q -9 zypper
        killall -q -9 packagekitd

        reponame="gbs-tools"
        repos=$(grep -E "(tizen\.org|otctools\.jf\.intel\.com)" /etc/zypp/repos.d/*.repo|awk -F: '{print $1}')
        # delete old repos
        for _repo in $repos
        do
            mv ${_repo} ${_repo}.backup 2>&1 >/dev/null
        done

        # set gbs repo
        zypper -q ar $(urlwrapper) $reponame
        zypper --no-gpg-checks --gpg-auto-import-keys --non-interactive refresh
    else
        echo "Unsupported distro: ${_distro}"
        exit
    fi

    # check if repo updated succeeded
    if [ ! $? -eq 0 ]
    then
        echo "Repositories updated failed."
        exit
    fi
    echo
}

# remove old version gbs
function gbs_remove()
{
    if [ "${_distro}" == "Ubuntu" ]; then
        for pkg in $(getmodules)
        do
            if dpkg -s $pkg 2>&1 >/dev/null
            then
                echo "Removing $pkg..."
                dpkg -r --force-depends $pkg >/dev/null
            fi
        done
        echo
        return
    fi

    for pkg in $(getmodules)
    do
        if rpm -q $pkg 2>&1 >/dev/null
        then
            echo "Removing $pkg..."
            rpm -e --nodeps $pkg >/dev/null
        fi
    done
    echo
}

function fedora_install()
{
    yum -y install gbs --nogpgcheck
}

function opensuse_install()
{
    zypper -n --no-gpg-checks install gbs
}

function ubuntu_install()
{
    apt-get -y --force-yes install gbs
}

function gbs_install()
{
   case "${_distro}" in
       Fedora)
           fedora_install
           ;;
       openSUSE)
           opensuse_install
           ;;
       Ubuntu)
           ubuntu_install
           ;;
       *)
           echo "Unsupported distro: ${_distro}"
           exit
           ;;
    esac
    echo
}

# delete miscs to avoid restarting system
function clean_miscs()
{
    for misc in ${binfmt_miscs}
    do
        if [ -e /proc/sys/fs/binfmt_misc/$misc ]; then
            chmod 666 /proc/sys/fs/binfmt_misc/$misc
            echo "-1" > /proc/sys/fs/binfmt_misc/$misc
        fi
    done
}

function clean_and_install()
{
    set_proxy
    # detect os type, store to _distro, _version, _id
    linux_distribution
    repo_update
    gbs_remove
    clean_miscs
    echo "Install gbs ..."
    gbs_install
}

function main()
{
    _repo_root=${_old_repo}
    clean_and_install
    _repo_root=${_new_repo}
    repo_update
    echo "Upgrading gbs ..."
    gbs_install
}

while getopts hi:o:n: OPTION
do
    for opt in ${opts}
    do
        case $OPTION in
            h)
                usage
                exit;;
            o)
                _old_repo=$OPTARG
                break;;
            n)
                _new_repo=$OPTARG
                break;;
            i)
                _repo_root=$OPTARG
                clean_and_install
                exit
                ;;
            *)
                echo "Invalid option!"
                exit;;
        esac

    done
done

main

echo
echo "Script Done"
