import os
import datetime
from collections import defaultdict
from bottle import route, run, static_file, redirect, view

from itest.runner import StatusFile

REPORT_DBPATH = '/home/test/webapp/reportdb/'
APP_PATH = os.path.dirname(os.path.abspath(os.path.relpath(__file__)))
os.chdir(APP_PATH)


def listdir(path):
    for name in os.listdir(path):
        aname = os.path.join(path, name)
        if os.path.isdir(aname):
            yield name, aname

def listdir_orderby_mtime(path):
    names = [ (name, os.stat(aname).st_mtime)
        for name, aname in listdir(path) ]
    names.sort(key=lambda i:i[1], reverse=True)
    names = [ name[0] for name in names ]
    return names


@route('/favicon.ico')
def favicon():
    return static_file('speech-balloon-green-g-icon.png',
                       os.path.join(APP_PATH, 'views'))


@route('/report')
def report_latest():
    names = listdir_orderby_mtime(REPORT_DBPATH)
    if names:
        return redirect('/report/%s' % names[0])
    return '<h1>No reports available</h1>'


@route('/report/list')
@view('report_list')
def report_list():
    names = listdir_orderby_mtime(REPORT_DBPATH)
    return {'names': names}


@route('/report/<report_id:re:[^/]+>')
@view('report_detail')
def report_detail(report_id):
    reports = find_reports(report_id)
    if not reports:
        return '<h1>No reports available</h1>'
    summary = make_summary(report_id, reports)
    return summary


@route('/report/<path:re:.+>')
def report_static_files(path):
    ext = os.path.splitext(path)[1]
    if ext in ('.log', '.case'):
        return static_file(path, REPORT_DBPATH, 'text/plain')
    return static_file(path, REPORT_DBPATH)


def find_reports(report_id):
    path = os.path.join(REPORT_DBPATH, report_id)
    reports = []
    for platform_id in os.listdir(path):
        log_path = os.path.join(path, platform_id)
        status_fname = os.path.join(log_path, 'STATUS')
        if not os.path.exists(status_fname):
            continue

        info = StatusFile(status_fname).load()
        reports.append((platform_id, info))
    return reports


def make_summary(report_id, reports):
    def attrs(key):
        return [ key(report) for _platform_id, report in reports ]

    total_cases = max(attrs(lambda r: r.start['total_cases']))
    version = ','.join(set(attrs(lambda r: dict(r.env).get('Target', ''))))
    start_date = ','.join(set(attrs(lambda r: r.start['start_time'][:10])))

    costs = attrs(lambda r: r.cost_seconds)
    max_cost = str(datetime.timedelta(seconds=max(costs)))
    mean_cost = str(datetime.timedelta(seconds=int(sum(costs) / len(costs))))

    col_names = set()
    row_names = set()
    matrix = defaultdict(dict)

    for platform_id, report in reports:
        env = dict(report.env)
        arch = env['Arch']
        dist = env['Dist']

        row_names.add(arch)
        col_names.add(dist)
        matrix[dist][arch] = (platform_id, report)

    def status(r):
        if not r.complete:
            return 'Running'
        if r.total['total'] == 0:
            return '0 Case'
        return '%%%d Pass' % (r.total['pass']*100/r.total['total'])

    row_names = sorted(row_names)
    col_names = sorted(col_names)
    table = []

    for arch in row_names:
        row = []
        for dist in col_names:
            if dist in matrix and arch in matrix[dist]:
                platform_id, report = matrix[dist][arch]
                txt = status(report)
                href = '/report/%s/%s/report.html' % (report_id, platform_id)
            else:
                txt = 'N/A'
                href = None
            row.append((txt, href))
        table.append(row)

    return {
        'total_cases': total_cases,
        'max_cost': max_cost,
        'mean_cost': mean_cost,
        'version': version,
        'start_date': start_date,
        'col_names': col_names,
        'row_names': row_names,
        'table': table,
        }


if __name__ == '__main__':
    run(host='0.0.0.0', port=8080)
