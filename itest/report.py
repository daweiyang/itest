#!/usr/bin/env python
# vim: set sw=4 ts=4 ai et:
import os
import cgi
from collections import defaultdict

from itest import msger
from itest.conf import settings

from mako.lookup import TemplateLookup

CWD = os.path.dirname(os.path.abspath(os.path.relpath(__file__)))
TEMPLATE_PATH = os.path.join(CWD, 'template')


class Report(object):

    def __init__(self, status):
        self.status = status


class TextReport(Report):

    def show(self):
        """show report on console"""
        if not self.status.complete:
            print 'Still running, %d cases total, %d remain' % (
                self.status.start['total_cases'],
                self.status.start['total_cases'] - self.status.total['total'])
        elif self.status.done['error']:
            print 'Planed to run %d cases but exit with %s' % (
                self.status.start['total_cases'], self.status.done['error'])

        if self.status.total['failed'] > 0:
            print
            msger.warning("Failed cases's logs are located at:")
            for case in self.status.failed:
                print
                print case['name']
                print '=============================='
                print case['log']
                print

        print
        print 'Ran %d tests in %s\n' % (
            self.status.total['total'],
            self.status.cost,
            )
        if self.status.total['failed'] == 0:
            print 'OK'
        else:
            print '%d Failed' % self.status.total['failed']
        print
        print 'Details'
        print '-------------------------------------'
        print '%-15s%s\t%s\t%s' % ('Component',
                                   'Passed',
                                   'Failed',
                                   'Total',
                                   )
        for comp, cnt in self.status.components.iteritems():
            print "%-15s%d\t%d\t%d" % (comp,
                                       cnt['pass'],
                                       cnt['failed'],
                                       cnt['total'],
                                       )
        print
        print 'More detail logs can be found at:', self.status.start['log_path']


class HTMLReport(Report):

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

    def show(self):
        html = self._generate()
        fname = "%s/report.html" % self.status.start['log_path']
        with open(fname, "w") as f:
            f.write(html)

        print 'HTML report was generated at:', fname
