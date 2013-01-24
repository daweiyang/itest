#!/usr/bin/env python
from distutils.core import setup
try:
    import setuptools
except ImportError:
    pass

from itest import __version__


setup(name='itest',
      version = __version__,
      description='Functional test framework',
      long_description='Functional test framework',
      author='Hui Wang, Yigang Wen, Daiwei Yang, Hao Huang, Junchun Guan',
      author_email='huix.wang@intel.com, yigangx.wen@intel.com, '
      'dawei.yang@intel.com, hao.h.huang@intel.com, junchunx.guan@intel.com',
      license='GPLv2',
      platforms=['Linux'],
      scripts=['runtest'],
      packages=['itest', 'itest.conf', 'itest.template'],
      package_data={'': ['*.html']},
      install_requires=["bottle>=0.10",
                        "pexpect",
                        "mako",
                        ],
     )
