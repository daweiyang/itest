import os
import shutil
import platform
import subprocess
from glob import glob

from itest import msger


def get_version():
    version = subprocess.check_output(['gbs', '--version'],
                                      stderr=subprocess.STDOUT)
    return version.split()[1]

def get_dependencies():
    deps = ['gbs',
            'depanneur',
            'osc',
            'build',
            'qemu-arm-static',
            'git-buildpackage-rpm',
            'git-buildpackage-common',
            'createrepo',
            'pristine-tar',
            ]

    dist = platform.dist()[0].lower()
    if dist == "ubuntu":
        deps.extend([
            'libcrypt-ssleay-perl',
            ])
    elif dist == "suse":
        deps.extend([
            'build-mkdrpms',
            'perl-Crypt-SSLeay',
            ])
    else:
        deps.extend([
            'perl-Crypt-SSLeay',
            ])
    return deps

# set osc certifications
OSC_CERT_DIR = os.path.expanduser('~/.config/osc/trusted-certs')
OSC_CERT_FROM = os.path.join(os.environ["ITEST_ENV_PATH"], 'fixtures', 'conf_fixtures')
OSC_CERTS = [name.split('/')[-1] for name in glob(r'%s/api.*_443.pem' % OSC_CERT_FROM)]

if not os.path.exists(OSC_CERT_DIR):
    os.makedirs(OSC_CERT_DIR)

try:
    for osc_cert in OSC_CERTS:
        if not os.path.exists(os.path.join(OSC_CERT_DIR, osc_cert)):
            shutil.copy(os.path.join(OSC_CERT_FROM, osc_cert), OSC_CERT_DIR)
except Exception, err:
    msger.error(str(err))

TARGET_NAME = 'gbs'
TARGET_VERSION = get_version()
DEPENDENCIES = get_dependencies()

SUDO_PASSWD = os.environ.get('ITEST_SUDO_PASSWD', '123456')
