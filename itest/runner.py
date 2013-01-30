import os
import sys
import json
import time
import datetime

from itest.utils import now
from itest.result import HTMLTestResult
from itest.signals import register_result


class TextTestRunner(object):

    result_class = HTMLTestResult

    def __init__(self, verbose):
        self.verbose = verbose

    def _make_result(self):
        return self.result_class(self.verbose)

    def run(self, test, space, env):
        print 'plan to run %d test%s' % (test.count, 's' if test.count > 1 else '')

        result = self._make_result()
        register_result(result)

        start_time = time.time()
        result.runner_start(test, space, env)
        try:
            test.run(result, space, self.verbose)
        except KeyboardInterrupt:
            result.stop(KeyboardInterrupt.__name__)
        except:
            result.runner_exception(sys.exc_info())
            raise
        finally:
            result.runner_stop()

        stop_time = time.time()
        cost = stop_time - start_time

        result.print_summary()
        run = len(result.success) + len(result.failure)

        print
        print 'Ran %d test%s in %.3fs' % (run,
            's' if run > 1 else '', cost)
        if result.was_successful:
            print 'OK'
        else:
            print '%d FAILED' % len(result.failure)


class StatusInfo(object):

    def __init__(self):
        self.cases = []
        self.complete = False

    def update(self, item):
        getattr(self, 'do_'+item['type'])(item)

    def do_start(self, item):
        self.start = item
        self.env = self.start['env']
        self.deps = self.start['deps']

    def do_case(self, item):
        self.cases.append(item)

    def do_done(self, item):
        if self.complete:
            return
        self.complete = True
        self.done = item

    def calculate(self):
        self.cal_cost()
        self.cal_cases()

    def cal_cost(self):
        stime = datetime.datetime.strptime(self.start['start_time'],
                                           '%Y-%m-%d %H:%M:%S')
        if self.complete:
            etime = datetime.datetime.strptime(self.done['end_time'],
                                               '%Y-%m-%d %H:%M:%S')
        else:
            etime = datetime.datetime.now()

        self.cost_seconds = int((etime - stime).total_seconds())
        self.cost = str(datetime.timedelta(seconds=self.cost_seconds))

    def cal_cases(self):
        components = {}
        comp2cases = {}
        failed = []
        for case in self.cases:
            comp = case['component']
            if comp not in components:
                components[comp] = {'pass': 0,
                                    'failed': 0,
                                    }
                comp2cases[comp] = []

            comp2cases[comp].append(case)
            cnt = components[comp]

            if case['exit_code'] == 0:
                cnt['pass'] += 1
                case['is_pass'] = True
            else:
                cnt['failed'] += 1
                failed.append(case)
                case['is_pass'] = False

        total = {'pass': 0,
                 'failed': 0,
                 }
        for cnt in components.values():
            for k, v in cnt.iteritems():
                total[k] += v
            cnt['total'] = sum(cnt.values())
        total['total'] = sum(total.values())

        self.total = total
        self.components = components
        self.comp2cases = comp2cases
        self.failed = failed


class StatusFile(object):
    '''Status and stat info of running tests'''

    def __init__(self, fname):
        self.fname = fname

    def log(self, data):
        msg = '|'.join([now(), json.dumps(data)]) + os.linesep
        with open(self.fname, 'a') as fp:
            fp.write(msg)

    def load(self):
        info = StatusInfo()
        with open(self.fname) as fp:
            for line in fp:
                _, data = line.split('|', 1)
                info.update(json.loads(data))
        info.calculate()
        return info

