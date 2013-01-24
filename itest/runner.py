import os
import sys
import json
import datetime

from itest import msger
from itest.utils import get_local_ipv4, now, get_dist, get_arch, query_pkg_info
from itest.case import sudo
from itest.conf import settings


class ConsoleRunner(object):

    def __init__(self, suite, verbose):
        self.suite = suite
        self.verbose = verbose
        self.log_path = suite.logdir
        self.stfp = StatusFile(os.path.join(self.log_path, 'STATUS'))
        self.lock_fname = os.path.join(self.suite.workspace, 'LOCK')
        self.locked = False

    def __del__(self):
        if self.locked:
            self.release_lock()

    def collect_env(self):
        env = [
            ('Dist', get_dist()),
            ('Arch', get_arch()),
            ('IP', get_local_ipv4()),
            ]
        if settings.TARGET_NAME:
            if settings.TARGET_VERSION:
                ver = settings.TARGET_VERSION
            else:
                ver = query_pkg_info(settings.TARGET_NAME)
            env.append(('Target',
                        '%s %s' % (settings.TARGET_NAME, ver)))
        return env

    def run_one(self, case):
        path = self.suite.prepare_env_for_one_case()
        os.chdir(path)

        msger.verbose(case.casename)
        case.run(self.verbose)

        if self.verbose:
            long_ = '(%s) %s' % (case.component,
                                 case.summary)
            log = msger.passed if case.exit_value == 0 else msger.failed
            log(long_)
        else:
            short = '.' if case.exit_value == 0 else 'F'
            sys.stdout.write(short)
        sys.stdout.flush()

    def _run(self):
        '''Run all the cases specified'''
        for case in self.suite.cases:
            try:
                self.run_one(case)
            except KeyboardInterrupt:
                choice = raw_input('''
Do you want abort or continue next case?
0-continue
1-abort
Please input 0 or 1:[0]''')
                if choice == '1':
                    raise
            finally:
                self.log_case(case)

    def log_start(self):
        env = self.collect_env()
        if settings.DEPENDENCIES:
            deps = [ (pkg, query_pkg_info(pkg))
                    for pkg in settings.DEPENDENCIES ]
        else:
            deps = []
        info = {
            'type': 'start',
            'start_time': now(),
            'workspace': self.suite.workspace,
            'log_path': self.log_path,
            'total_cases': len(self.suite.cases),
            'env': env,
            'deps': deps,
        }
        self.stfp.log(info)

    def log_done(self, error):
        info = {
            'type': 'done',
            'error': error,
            'end_time': now(),
        }
        self.stfp.log(info)

    def log_case(self, case):
        #TODO: deal with the situation that run case failed and
        # these attributes are not all set correctly
        info = {
            'type': 'case',
            'start_time': case.start_time,
            'end_time': now(),
            'name': case.casename,
            'file': os.path.join(self.log_path, case.casename),
            'log': case.log_path,
            'component': case.component,
            'exit_code': case.exit_value,
            'issue': case.issue,
            'id': case.id,
            }
        self.stfp.log(info)

    def prepare(self):
        if not self.acquire_lock():
            msger.error("another instance is working on this workspace(%s) "
                        "since the lock file(%s) exist. please run ps to "
                        "check." % (self.suite.workspace, self.lock_fname))
            return False

        self.suite.setup_workspace()
        self.log_start()
        return True

    def run(self):
        msger.info('testing start')
        err = ''
        try:
            return self._run()
        except (Exception, KeyboardInterrupt) as err:
            err = '%s:%s' % (err.__class__.__name__, str(err))
            raise
        finally:
            self.log_done(err)

    def status_info(self):
        return self.stfp.load()

    def acquire_lock(self):
        if os.path.exists(self.lock_fname):
            return False

        workspace = self.suite.workspace
        if os.path.exists(workspace):
            msger.info('removing old workspace %s' % workspace)
            if sudo('rm -rf %s' % workspace) != 0:
                msger.error("can't clean old workspace, please fix manually")

        os.mkdir(workspace)
        open(self.lock_fname, 'w').close()
        self.locked = True
        return True

    def release_lock(self):
        try:
            os.unlink(self.lock_fname)
        except OSError, err:
            if err.errno == 2: #No such file or directory
                msger.warning("lock file(%s) should be there, "
                              "but it doesn't exist" % self.lock_fname)
            else:
                raise

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

