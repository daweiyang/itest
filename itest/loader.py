import os
import re

from itest.case import TestCase
from itest.suite import TestSuite
from itest import msger


class SectionParser(object):

    def __init__(self):
        self._lineno = 0
        self._current_section_name = None
        self._concat_to_last_line = False
        self.sections = {}
        self.filename = '<noname>'

    def parse(self, fname):
        fname = os.path.abspath(fname)
        self.filename = fname
        with open(fname) as f:
            return self.parse_string(f.read())

    def parse_string(self, text):
        for line in text.splitlines():
            self._lineno += 1
            if line.startswith('#'):
                continue
            elif line.startswith('__'): # section header
                self._open_a_new_section(line)
            else:
                self._append_section_content(line)

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
            raise SyntaxError('%d:Content outside section:%s' % (self._lineno, line))
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


class CaseParser(SectionParser):

    def parse_string(self, text):
        super(CaseParser, self).parse_string(text)

        summary = self._parse_summary()
        steps = self._parse_steps()
        qa = self._parse_qa()
        issue = self._parse_issue()
        teardown = self._parse_teardown()

        return TestCase(self.filename, summary, steps,
                        qa=qa,
                        issue=issue,
                        teardown=teardown,
                        )

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

    def _parse_teardown(self):
        if not 'teardown' in self.sections:
            return ()
        return self.sections['teardown']

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


class TestLoader(object):

    case_parser_class = CaseParser

    def load_args(self, args, env):
        if not args:
            path = os.path.join(env.ENV_PATH, env.CASES_DIR)
            return self.load_from_dir(path)

        suite = TestSuite()
        for arg in args:
            if arg in env.SUITES:
                test = self.load(env.SUITES[arg], env)
            else:
                test = self.load(arg, env)
            if test:
                suite.add_test(test)
        return suite

    def load(self, sel, env):
        # case file
        if os.path.isfile(sel):
            return self.load_from_file(sel)

        # directory which contains cases
        if os.path.isdir(sel):
            return self.load_from_dir(sel)

        #component name which is the first-level child name of ENV cases path
        comp = self.guess_components(env)
        if sel in comp:
            return self.load_component(env, sel)

        return self._load_registered_pattern(sel, env)

    def _load_registered_pattern(self, sel, env):
        for cls in suite_patterns.all():
            test = cls().load(sel, env)
            if test:
                return test

    def load_from_file(self, name):
        path = os.path.abspath(name)

        parser = self.case_parser_class()
        try:
            test = parser.parse(path)
        except SyntaxError, err:
            msger.error('%s:%s' % (name, err))
        else:
            return test

    def load_from_dir(self, top):
        suite = TestSuite()

        for name in self._walk(top):
            test = self.load_from_file(name)
            if test:
                suite.add_test(test)
        return suite

    def _walk(self, top):
        for current, _dirs, nondirs in os.walk(top):
            for name in nondirs:
                if name.endswith('.case'):
                    yield os.path.join(current, name)

    def guess_components(self, env):
        comp = []
        path = os.path.join(env.ENV_PATH, env.CASES_DIR)
        for base in os.listdir(path):
            full = os.path.join(path, base)
            if os.path.isdir(full):
                comp.append(base)
        return comp

    def load_component(self, env, comp):
        path = os.path.join(env.ENV_PATH, env.CASES_DIR, comp)
        return self.load_from_dir(path)


class InverseComponent(object):

    def load(self, sel, env):
        if not sel.startswith('!'):
            return

        loader = TestLoader()
        excluding = sel[1:]
        comps = loader.guess_components(env)
        if excluding not in comps:
            return

        suite = TestSuite()
        for comp in comps:
            if comp != excluding:
                test = loader.load_component(env, comp)
                suite.add_test(test)

        return suite


class _SuitePatternRegister(object):

    def __init__(self):
        self._patterns = []

    def register(self, cls):
        self._patterns.append(cls)

    def all(self):
        return self._patterns


suite_patterns = _SuitePatternRegister()
suite_patterns.register(InverseComponent)
