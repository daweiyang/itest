#!/usr/bin/env python
# vim: set sw=4 ts=4 ai et:
import os
import uuid
import shutil

from itest.conf import settings
from itest.case import TestCase
from itest import msger


class TestSuite(object):
    '''Contains cases list and corresponding fixtures'''

    def __init__(self, case_fnames):
        self.workspace = settings.WORKSPACE
        self.case_fnames = case_fnames
        self.logdir = os.path.join(self.workspace, 'logs')
        self.running_dir = os.path.join(self.workspace, 'running')
        self.fixtures_dir = os.path.join(self.workspace, 'fixtures')
        self.cases = self._generate_cases(case_fnames)

    def setup_workspace(self):
        os.makedirs(self.logdir)
        os.makedirs(self.running_dir)
        self._copy_cases(self.case_fnames)
        self._copy_fixtures()

    def _copy_cases(self, case_fnames):
        for fname in case_fnames:
            shutil.copy(fname, self.logdir)

    def _copy_fixtures(self):
        from_ = os.path.join(settings.ENV_PATH, settings.FIXTURES_DIR)
        shutil.copytree(from_, self.fixtures_dir)

    def _generate_cases(self, case_fnames):
        '''Generate test cases'''
        cases = []
        for fname in case_fnames:
            try:
                case = TestCase(self, fname)
            except SyntaxError, err:
                msger.error('%s:%s' % (fname, err))
            cases.append(case)
        return cases

    def prepare_env_for_one_case(self):
        dirname = str(uuid.uuid4()).replace('-', '')
        path = os.path.join(self.running_dir, dirname)
        os.mkdir(path)
        os.mkdir(os.path.join(path, TestCase.meta_path_name))

        for fname in os.listdir(self.fixtures_dir):
            source = os.path.join(self.fixtures_dir, fname)
            target = os.path.join(path, fname)

            if os.path.isdir(source):
                shutil.copytree(source, target)
            else:
                shutil.copy(source, target)

        return path
