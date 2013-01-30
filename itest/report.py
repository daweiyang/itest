# vim: set sw=4 ts=4 ai et:
import os
import cgi
from collections import defaultdict

from itest.conf import settings

from mako.lookup import TemplateLookup

CWD = os.path.dirname(os.path.abspath(os.path.relpath(__file__)))
TEMPLATE_PATH = os.path.join(CWD, 'template')


class HTMLReport(object):

    def __init__(self, status):
        self.status = status

    def format(self, string, *args):
        trans = lambda i: cgi.escape(i) if isinstance(i, basestring) else i
        return string % tuple([trans(i) for i in args])

    def issue_link(self, issue_no):
        return "https://otctools.jf.intel.com/pm/issues/%s" % issue_no

    def _generate(self):
        '''Collect test results and generate a html report'''
        comp2issues = defaultdict(set)
        for case in self.status.cases:
            issue = case['issue']
            if issue:
                comp = case['component']
                for i in issue:
                    comp2issues[comp].add(i)

        issue2cases = defaultdict(list)
        for case in self.status.cases:
            if case['issue']:
                for i in case['issue']:
                    issue2cases[i].append(case)

        data = {'status': self.status,
                'comp2issues': comp2issues,
                'issue_link': self.issue_link,
                'issue2cases': issue2cases,
                'basename': os.path.basename,
                }
        return self._render(data)

    def _render(self, data):
        data.update(settings.REPORT_CONTEXT)

        template_dirs = [TEMPLATE_PATH]
        fname = os.path.join(settings.ENV_PATH, settings.REPORT_TEMPLATE_FILE)
        if os.path.exists(fname):
            path = os.path.dirname(fname)
            template_dirs.insert(0, path)
            tpl = os.path.basename(fname)
        else:
            tpl = 'default.html'

        lookup = TemplateLookup(directories=template_dirs,
                                output_encoding='utf-8')
        template = lookup.get_template(tpl)
        return template.render(**data)

    def generate(self):
        html = self._generate()
        fname = "%s/report.html" % self.status.start['log_path']
        with open(fname, "w") as f:
            f.write(html)

        print
        print 'HTML report was generated at:', fname
