import os
WORKSPACE = os.path.expanduser('~/testspace')


CASES_DIR = 'cases'
FIXTURES_DIR = 'fixtures'


# Auto sync will upload testing logs and report to this URL
UPLOAD_URL = 'test@testvm:/home/test/webapp/reportdb/%(date)s/%(dist)s_%(arch)s'


# Mapping from suite name to a list of cases.
# For example, an ENV can have special suite names such as "Critical" and
# "CasesUpdatedThisWeek", which include different set of cases.
# Then refer it in command line as:
# $ runtest Critical
# $ runtest CasesUpdatedThisWeek
SUITES = {}


# Define testing target name and version. They can be showed in console info
# or title or HTML report. But if TARGET_NAME is None, it will show nothing
TARGET_NAME = None

# If TARGET_NAME is not None, but TARGET_VERSION is None, version will be got
# by querying package TARGET_NAME. If TARGET_VERSION is not None, simply use it
TARGET_VERSION = None

# List of package names as dependencies. This info can be show in report.
DEPENDENCIES = []


# Password to run sudo.
SUDO_PASSWD = os.environ.get('ITEST_SUDO_PASSWD')


# Customized HTML report template. A relative path to ENV path.
# It's a Mako template which can inherit from the default template "basic.html"
# and then write its special content.
# Refer http://www.makotemplates.org/ for how to write
REPORT_TEMPLATE_FILE = 'report.html'

# Additional variable to render customized template
REPORT_CONTEXT = {}

# Enable python-coverage report
ENABLE_COVERAGE = False

# Customized python-coverage rcfile
COVERAGE_RCFILE = 'coveragerc'