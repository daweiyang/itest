# vim: set sw=4 ts=4 ai et:
import os
import sys

from itest.conf import settings
from itest import msger

import pexpect


def pcall(cmd, args=(), expecting=(), timeout=None, output=None):
    '''call cmd with expecting
    expecting: list of pairs, first is expecting string, second is send string
    timeout: in seconds, default is None(block forever)
    redirect: redirect cmd stdout and stderr to file object
    '''

    question = [pexpect.EOF, pexpect.TIMEOUT] + \
        [ pair[0] for pair in expecting ]
    answer = [None, None] + [ pair[1] for pair in expecting ]

    child = pexpect.spawn(cmd, list(args))
    if output:
        child.logfile_read = output

    try:
        while True:
            i = child.expect(question, timeout=timeout)
            if i < 2:
                break
            child.sendline(answer[i])
    except:
        raise
    finally:
        child.close()

    return child.exitstatus


def sudo(cmd):
    '''sudo command automatically input password'''
    cmd = 'sudo ' + cmd
    msger.info(cmd)

    expecting = [('[p|P]assword', settings.SUDO_PASSWD)]
    return pcall(cmd, expecting=expecting, timeout=60, output=sys.stdout)


class Tee(object):

    '''data write to original will write to another as well'''

    def __init__(self, original, another=sys.stdout):
        self.original = original
        self.another = another

    def write(self, data):
        self.another.write(data)
        return self.original.write(data)

    def flush(self):
        self.another.flush()
        return self.original.flush()

    def close(self):
        self.original.close()


class TestCase(object):
    '''Single test case'''

    meta = '.itest'
    count = 1
    was_successful = False

    def __init__(self, fname, summary, steps, qa=(), issue=None, teardown=()):
        self.filename = fname
        self.summary = summary
        self.steps = steps
        self.qa = qa
        self.issue = issue
        self.teardown = teardown
        self.component = self.guess_component(self.filename)
        #TODO: need a more reasonable and meaningful id rather than this
        self.id = hash(self)
        self.start_time = None
        self.logname = None
        self.rundir = None
        self.script = None
        self.teardown_script = None

    def __hash__(self):
        return hash(self.filename)

    def __eq__(self, that):
        return hash(self) == hash(that)

    def guess_component(self, filename):
        # assert that filename is absolute path
        cases_dir = os.path.join(settings.ENV_PATH, settings.CASES_DIR)
        if not filename.startswith(cases_dir):
            return 'unknown'
        relative = filename[len(cases_dir)+1:].split(os.sep)
        # >1 means [0] is an dir name
        return relative[0] if len(relative) > 1 else 'unknown'

    def _prepare(self, space):
        self.rundir = space.new_test_dir()
        os.chdir(self.rundir)
        self.logname = space.new_log_name(self)
        os.mkdir(self.meta)
        self.script = self._generate_run()
        if self.teardown:
            self.teardown_script = self._generate_script('teardown', self.teardown)

    def _set_up(self):
        pass

    def _tear_down(self, verbose):
        if self.teardown:
            return self._run_script(self.teardown_script, verbose)

    def _run_cmd(self, verbose):
        return self._run_script(self.script,
                                verbose,
                                '-xe',
                                self.qa)

    def _run_script(self, path, verbose, bash_opts='-x', more_expecting=()):
        expecting = [('[p|P]assword', settings.SUDO_PASSWD)] + list(more_expecting)
        with open(self.logname, 'a') as log:
            if verbose and verbose > 1:
                log = Tee(log)
            return pcall('/bin/bash',
                         [bash_opts, path],
                         expecting=expecting,
                         timeout=settings.RUN_CASE_TIMEOUT,
                         output=log)

    def run(self, result, space, verbose):
        result.test_start(self)

        try:
            self._prepare(space)
            self._set_up()

            try:
                exit_status = self._run_cmd(verbose)
            finally: # make sure to call tearDown if setUp success
                self._tear_down(verbose)
                self.delete_color_code_in_log_file(self.logname)

            if exit_status == 0:
                result.add_success(self)
            else:
                result.add_failure(self)
        except KeyboardInterrupt:
            raise
        except:
            result.add_exception(self, sys.exc_info())
        finally:
            result.test_stop(self)

    def delete_color_code_in_log_file(self, fname):
        os.system("sed -i 's/\x1b\[[0-9]*m//g' %s" % fname)

    def _run_with_coverage(self, pre):
        rcfile = os.path.join(settings.ENV_PATH, settings.COVERAGE_RCFILE)
        if os.path.exists(rcfile):
            rcopt = '--rcfile %s' % rcfile
        else:
            rcopt = ''

        target = settings.TARGET_NAME
        fake_target = os.path.join(self.meta, target)
        logpath = os.path.dirname(self.logname)

        with open(fake_target, 'w') as f:
            print >> f, '''#!/bin/bash
coverage run -p %s $ITEST_ORIG_TARGET "$@"
status=$?
[ -e .coverage* ] && mv .coverage* %s
exit $status
''' % (rcopt, logpath)

        pre.extend(['export ITEST_ORIG_TARGET=$(which %s)' % target,
                    'chmod +x %s' % fake_target,
                    'export PATH=$(pwd)/%s:$PATH' % self.meta,
                    ])

    def _generate_run(self):
        pre = ['set +x',
            ]
        if settings.ENABLE_COVERAGE:
            self._run_with_coverage(pre)
        pre.extend(['set -o pipefail',
                    'set -x'])
        return self._generate_script('run', pre + self.steps)

    def _generate_script(self, name, cmds):
        path = os.path.join(self.meta, name)
        content = os.linesep.join(cmds)
        with open(path, 'w') as f:
            f.write(content)
        return path
