import os

from itest.utils import query_pkg_info


class TestEnv(object):

    def __init__(self, env_settings):
        self.settings = env_settings

    def __getattr__(self, name):
        if name == name.upper():
            return getattr(self.settings, name)
        raise AttributeError("has no attribute %s" % name)

    @property
    def cases_dir(self):
        return os.path.join(self.ENV_PATH, self.CASES_DIR)

    @property
    def fixtures_dir(self):
        return os.path.join(self.ENV_PATH, self.FIXTURES_DIR)

    def query_target(self):
        name = self.TARGET_NAME
        if not name:
            return

        ver = self.TARGET_VERSION
        if not ver:
            ver = query_pkg_info(name)

        return (name, ver)

    def query_dependencies(self):
        deps = self.DEPENDENCIES
        if deps:
            return [ (pkg, query_pkg_info(pkg))
                     for pkg in deps ]
