#!/usr/bin/env python
# vim: set sw=4 ts=4 ai et:
import os
import re
import sys
import itertools

from itest.conf import settings
from itest.utils import now
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


class CaseManager(object):

    def __init__(self):
        self.cases_path = os.path.join(settings.ENV_PATH,
                                       settings.CASES_DIR)
        self.components = [ name
            for name in os.listdir(self.cases_path)
            if os.path.isdir(os.path.join(self.cases_path, name)) ]

    def _find_recursively(self, top):
        cases = [
            map(lambda name: os.path.join(current, name),
            filter(lambda name: name.endswith('.case'), nondirs))
            for current, _dirs, nondirs in os.walk(top) ]
        return itertools.chain(*cases)

    def find_one(self, sel):
        # case file
        if os.path.isfile(sel):
            return [ os.path.abspath(sel) ]

        # directory which contains cases
        if os.path.isdir(sel):
            return self._find_recursively(os.path.abspath(sel))

        #suite name defined in ENV settings
        if sel in settings.SUITES:
            return settings.SUITES[sel]

        #component name which is the first-level child name of ENV cases path
        if sel in self.components:
            path = os.path.join(self.cases_path, sel)
            return self._find_recursively(path)

        return []

    def find(self, selector):
        cases = []

        if not selector:
            cases = self._find_recursively(self.cases_path)
        elif hasattr(selector, '__iter__'):
            for sel in selector:
                cases.extend(self.find_one(sel))
        else:
            cases = self.find_one(selector)

        cases = list(set(cases))
        cases.sort()

        #FIXME: should shuffle cases before testing
        # but now GBS build cases can't be shuffled
        #random.shuffle(cases)
        return cases


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


class CaseParser(object):

    def __init__(self, lines):
        self._lineno = 0
        self._current_section_name = None
        self._concat_to_last_line = False
        self.sections = {}

        self._parse(lines)

    def _open_a_new_section(self, line):
        def split_header(line):
            pos = line.find(':')
            if pos != -1:
                name, remain = line[:pos], line[pos+1:].strip()
            else:
                name = line
                remain = ''
            name = name.strip('_ \t\r\n').lower()

            if not name:
                raise SyntaxError('%d:Invalid section header:%s' % \
                    (self._lineno, line))
            return name, remain

        name, remain = split_header(line)
        if name in self.sections:
            raise SyntaxError('%d:Duplicate section:%s' % (self._lineno, line))
        self._current_section_name = name
        self.sections[name] = []
        self._append_section_content(remain)

    def _append_section_content(self, line):
        name = self._current_section_name
        if not name:
            raise SyntaxError('%d:Content outside section:%s' % \
                (self._lineno, line))
        line = line.rstrip('\r\n')
        if line.endswith('\\'):
            self._concat_to_last_line = True
            line = line[:-1]
            self.sections[name].append(line)
        elif self._concat_to_last_line:
            self._concat_to_last_line = False
            self.sections[name][-1] += line
        else:
            self.sections[name].append(line)

    def _parse_text(self, lines):
        for line in lines:
            self._lineno += 1
            if line.startswith('#'):
                continue
            elif line.startswith('__'): # section header
                self._open_a_new_section(line)
            else:
                self._append_section_content(line)

    def _parse(self, lines):
        self._parse_text(lines)
        self.summary = self._parse_summary()
        self.steps = self._parse_steps()
        self.qa = self._parse_qa()
        self.issue = self._parse_issue()

    def _parse_summary(self):
        if not 'summary' in self.sections:
            raise SyntaxError('Summary section is required')
        return '\n'.join([line for line in self.sections['summary'] if line])

    def _parse_steps(self):
        if not 'steps' in self.sections:
            raise SyntaxError('Steps section is required')

        return [ line[1:].lstrip()
                for line in self.sections['steps']
                if line.startswith('>') ]

    def _parse_qa(self):
        if not 'qa' in self.sections:
            return []

        qa = []
        state = 0
        question = None
        answer = None

        for line in self.sections['qa']:
            line = line.rstrip(os.linesep)
            if not line:
                continue

            if state == 0 and line.startswith('Q:'):
                question = line[len('Q:'):].lstrip()
                state = 1
            elif state == 1 and line.startswith('A:'):
                # add os.linesep here to simulate user input enter
                answer = line[len('A:'):].lstrip() + os.linesep
                state = 2
            elif state == 2 and line.startswith('Q:'):
                qa.append((question, answer))
                question = line[len('Q:'):].lstrip()
                state = 1
            else:
                raise SyntaxError('Invalid format of QA:%s' % line)

        if state == 2:
            qa.append((question, answer))

        return qa

    def _parse_issue(self):
        if not 'issue' in self.sections:
            return None

        txt = '\n'.join(self.sections['issue']).strip()
        if not txt:
            return []

        nums = []
        issues = txt.replace(',', ' ').split()
        for issue in issues:
            m = re.match(r'(#|(feature|bug|issue)(-)?)?(\d+)', issue, re.I)
            if m:
                nums.append(m.group(4))

        if not nums:
            raise SyntaxError('Unrecognized issue number:%s' % txt)
        return nums



class TestCase(object):
    '''Class of single test case.'''

    parser_cls = CaseParser
    meta_path_name = '.itest'

    def __init__(self, suite, fname):
        self.suite = suite
        self.casename = os.path.basename(fname)
        self.log_path = os.path.join(suite.logdir, self.casename + '.log')
        self.component = self.guess_component(fname)
        #change self.is_pass to self.exit_value, specify it with
        #these possible values, None : not excuted, 0 : passed,
        #other integers : failed
        self.exit_value = None
        self.parse_case(fname)
        #TODO: need a more reasonable and meaningful id rather than this
        self.id = hash(self.casename)

    def guess_component(self, filename):
        # assert that filename is absolute path
        cases_dir = os.path.join(settings.ENV_PATH, settings.CASES_DIR)
        if not filename.startswith(cases_dir):
            return 'unknown'
        relative = filename[len(cases_dir)+1:].split(os.sep)
        # >1 means [0] is an dir name
        return relative[0] if len(relative) > 1 else 'unknown'

    def parse_case(self, fname):
        with open(fname) as fp:
            parser = self.parser_cls(fp)

        self.summary = parser.summary
        self.steps = parser.steps
        self.expecting = [ ('[p|P]assword', settings.SUDO_PASSWD) ] + parser.qa
        self.issue = parser.issue

    def logcat(self):
        """display the log of test case"""
        if os.path.exists(self.log_path):
            os.system('/bin/cat %s' % self.log_path)

    def run(self, verbose):
        script = self._generate_script(self.steps)
        self.start_time = now()

        with open(self.log_path, 'w') as log:
            if verbose and verbose > 1:
                log = Tee(log)
            # all steps exit 0 means testing is passed
            self.exit_value = pcall('/bin/bash', ['-xe', script],
                                    expecting=self.expecting,
                                    timeout=6*60*60,
                                    output=log)

        self.delete_color_code_in_log_file(self.log_path)
        return self.exit_value

    def delete_color_code_in_log_file(self, fname):
        os.system("sed -i 's/\x1b\[[0-9]*m//g' %s" % fname)

    def _run_with_coverage(self, pre):
        rcfile = os.path.join(settings.ENV_PATH, settings.COVERAGE_RCFILE)
        if os.path.exists(rcfile):
            rcopt = '--rcfile %s' % rcfile
        else:
            rcopt = ''

        target = settings.TARGET_NAME
        fake_target = os.path.join(self.meta_path_name, target)
        logpath = os.path.dirname(self.log_path)

        with open(fake_target, 'w') as f:
            print >> f, '''#!/bin/bash
coverage run -p %s $ITEST_ORIG_TARGET "$@"
status=$?
[ -e .coverage* ] && mv .coverage* %s
exit $status
''' % (rcopt, logpath)

        pre.extend(['export ITEST_ORIG_TARGET=$(which %s)' % target,
                    'chmod +x %s' % fake_target,
                    'export PATH=$(pwd)/%s:$PATH' % self.meta_path_name,
                    ])

    def _generate_script(self, steps):
        name = os.path.join(self.meta_path_name, 'run')
        pre = ['set +x',
            'set -o pipefail',
            ]

        if settings.ENABLE_COVERAGE:
            self._run_with_coverage(pre)

        pre.extend(['set -x'])

        content = os.linesep.join(pre + steps)
        with open(name, 'w') as f:
            f.write(content)
        return name
