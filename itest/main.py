#!/usr/bin/env python
# vim: set sw=4 ts=4 ai et:
import os
import re
import time
import signal
from argparse import ArgumentParser
from threading import Thread, Event

from itest import msger
from itest.conf import settings, ENVIRONMENT_VARIABLE
from itest.case import CaseManager
from itest.suite import TestSuite
from itest.utils import get_dist, get_arch
from itest.runner import ConsoleRunner, StatusFile
from itest.report import TextReport, HTMLReport
from itest.error import SIGErr, sighandle


def rsync(local_path, remote_path):
    cmd = "rsync -a '%s/'* '%s'" % (local_path, remote_path)
    msger.debug(cmd)
    ret = os.system(cmd)
    if ret == 0:
        return 0

    msger.warning('sync to %s failed, time a few seconds and retry')
    time.sleep(5)
    ret = os.system(cmd)
    if ret == 0:
        return 0

    msger.warning('sync to %s failed, please check the network')
    return ret


def start_sync_worker(local_path, remote_path, to_die, interval):
    def _thread():
        while 1:
            if to_die.wait(interval):
                break

            #FIXME: eliminate the message print out every interval
            make_report(local_path)
            if rsync(local_path, remote_path) != 0:
                msger.warning('sync thread exit, please sync manually')
                break
        msger.info('sync thread exit')

    proc = Thread(target=_thread)
    proc.start()
    return proc


def transform_url(url):
    if not url:
        url = settings.UPLOAD_URL

    if re.search(r'%\(.*?\)s', url):
        data = {'date': time.strftime('%Y%m%d'),
                'dist': get_dist(),
                'arch': get_arch(),
                }
        return url % data
    return url


def mkdir_in_remote(url):
    parts = url.split('@', 1)
    if len(parts) > 1:
        username, host_and_path = parts
    else:
        host_and_path = parts[0]
        username = ''
    host, path = host_and_path.split(':', 1)
    userhost = '%s@%s' % (username, host) if username else host

    cmd = "ssh '%s' mkdir -p '%s'" % (userhost, path)
    msger.debug(cmd)
    if os.system(cmd) != 0:
        msger.error("can't mkdir %s in remote server %s" % (path, userhost))


def run_test(args):
    mgr = CaseManager()
    case_fnames = mgr.find(args.cases)
    if not case_fnames:
        print 'No case found'
        return

    suite = TestSuite(case_fnames)
    runner = ConsoleRunner(suite, args.verbose)
    if not runner.prepare():
        return

    to_upload = args.auto_sync or args.url
    if to_upload:
        url = transform_url(args.url)
        mkdir_in_remote(url)

    if args.auto_sync:
        msger.info('automatically upload report ot %s' % url)
        to_die = Event()
        thread = start_sync_worker(runner.log_path, url, to_die, args.interval)

    def make_report_and_upload():
        if args.auto_sync:
            to_die.set()
            thread.join()

        make_report(runner.log_path)
        if to_upload:
            rsync(runner.log_path, url)

    try:
        runner.run()
    except KeyboardInterrupt:
        print '\nAbort!'
    except SIGErr, err:
        print '\n', err
    finally:
        make_report_and_upload()


def make_report(log_path):
    make_coverage_report(log_path)

    info = StatusFile(os.path.join(log_path, 'STATUS')).load()
    for cls in (TextReport, HTMLReport):
        cls(info).show()


def make_coverage_report(log_path):
    if not settings.ENABLE_COVERAGE:
        return

    cmds = ['cd %s' % log_path,
            'python-coverage combine',
            'python-coverage report -m',
            'rm -rf htmlcov',
            'python-coverage html',
            ]
    os.system(';'.join(cmds))


def guess_env():
    if ENVIRONMENT_VARIABLE not in os.environ and os.path.exists('settings.py'):
        os.environ[ENVIRONMENT_VARIABLE] = os.getcwd()


def main():
    guess_env()

    #define sorts of signal handler
    signal.signal(signal.SIGTERM, sighandle)

    parser = ArgumentParser(description='an testing framework for tools')
    parser.add_argument('cases', nargs='*',
        help='case files or suite names defined in settings.py')
    parser.add_argument('-v', '--verbose', action='count',
        help='verbose information')
    parser.add_argument('-d', '--debug', action='store_true',
        help='print debug information')
    parser.add_argument('--auto-sync', action='store_true',
        help='automatically upload report to server specified by --url. ')
    parser.add_argument('--url', help='overwrite default url of server. '
                        'default is: %s' % settings.UPLOAD_URL.replace('%', '%%'))
    parser.add_argument('--interval', type=int, default=60*5,
                        help='interval that upload report to --url')
    parser.add_argument('--report', action='store_true',
                        help='make report from current running status')

    args = parser.parse_args()
    if args.verbose:
        msger.set_loglevel('verbose')
    if args.debug:
        msger.set_loglevel('debug')

    if args.report:
        log_path = os.path.join(settings.WORKSPACE, 'logs')
        make_report(log_path)
    else:
        run_test(args)


if __name__ == '__main__':
    main()
