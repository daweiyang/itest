import os
import sys
import time
import json
import traceback

from itest.utils import get_local_ipv4, now, get_dist, get_arch


class TestResult(object):

    success = []
    failure = []
    should_stop = False
    stop_reason = None

    def __init__(self, verbose=0):
        self.verbose = verbose

    def test_start(self, test):
        '''test case start'''
        test.start_time = time.time()

    def test_stop(self, test):
        '''test case stop'''
        test.cost_time = time.time() - test.start_time

    def runner_start(self, test, space, env):
        '''test runner start'''
        self.start_time = time.time()

    def runner_stop(self):
        '''test runner stop'''
        self.cost_time = time.time() - self.start_time

    def runner_exception(self, exc_info):
        type_, value, tb = exc_info
        traceback.print_exception(type_, value, tb)
        del tb

    def add_success(self, test):
        test.was_successful = True
        self.success.append(test)

    def add_failure(self, test):
        test.was_successful = False
        self.failure.append(test)

    def add_exception(self, test, exc_info):
        type_, value, tb = exc_info
        traceback.print_exception(type_, value, tb)
        del tb
        test.was_successful = False
        self.failure.append(test)

    @property
    def was_successful(self):
        return len(self.failure) == 0

    def stop(self, reason):
        print 'try to stop since', reason
        self.should_stop = True
        self.stop_reason = reason


class TextTestResult(TestResult):

    def add_success(self, test):
        super(TextTestResult, self).add_success(test)
        if self.verbose:
            print os.path.basename(test.filename), '... ok'
        else:
            sys.stdout.write('.')
        sys.stdout.flush()

    def add_failure(self, test):
        super(TextTestResult, self).add_failure(test)
        if self.verbose:
            print '-' * 40
            print '[FAILED]', os.path.basename(test.filename)
            print 'case    ', test.filename
            print 'rundir  ', test.rundir
            print 'logname ', test.logname
        else:
            sys.stdout.write('F')
        sys.stdout.flush()

    def print_summary(self):
        if not self.failure:
            return

        print
        print '=' * 40
        print 'Failure detail'
        for test in self.failure:
            print
            print os.path.basename(test.filename)
            print 'case    ', test.filename
            print 'rundir  ', test.rundir
            print 'logname ', test.logname


class HTMLTestResult(TextTestResult):

    def runner_start(self, test, space, env):
        super(HTMLTestResult, self).runner_start(test, space, env)
        self.status_path = os.path.join(space.logdir, 'STATUS')
        self._log_start(space, env, test)

    def runner_stop(self):
        super(HTMLTestResult, self).runner_stop()
        self._log_stop(self.stop_reason)

    def runner_exception(self, exc_info):
        super(HTMLTestResult, self).runner_exception(exc_info)
        self._log_stop(str(exc_info[1]))

    def test_stop(self, test):
        super(HTMLTestResult, self).test_stop(test)
        self._log_case(test)

    def _collect_env(self, env):
        items = [
            ('Dist', get_dist()),
            ('Arch', get_arch()),
            ('IP', get_local_ipv4()),
            ]
        target = env.query_target()
        if target:
            items.append(('Target', str(target)))
        return items

    def _log_start(self, space, env, test):
        info = {
            'type': 'start',
            'start_time': now(),
            'workspace': space.workdir,
            'log_path': space.logdir,
            'total_cases': test.count,
            'env': self._collect_env(env),
            'deps': env.query_dependencies(),
        }
        self._dump(info)

    def _log_stop(self, why):
        info = {
            'type': 'done',
            'error': str(why) if why else '',
            'end_time': now(),
        }
        self._dump(info)

    def _log_case(self, test):
        info = {
            'type': 'case',
            'start_time': test.start_time,
            'cost_time': test.cost_time,
            'name': os.path.basename(test.filename),
            'file': test.filename,
            'log': test.logname,
            'component': test.component,
            'exit_code': 0 if test.was_successful else 1,
            'issue': test.issue,
            'id': test.id,
            }
        self._dump(info)

    def _dump(self, data):
        msg = '|'.join([now(), json.dumps(data)]) + os.linesep
        with open(self.status_path, 'a') as f:
            f.write(msg)
