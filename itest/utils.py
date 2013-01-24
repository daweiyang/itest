#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright (c) 2009, 2010, 2011 Intel, Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; version 2 of the License
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 59
# Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import re
import datetime
import platform
import subprocess


def proxy_unset():
    os.unsetenv('http_proxy')
    os.unsetenv('https_proxy')
    os.unsetenv('no_proxy')

def get_local_ipv4():
    inet_addr = re.compile(r'(inet\s+|inet addr:)([\d\.]+)')
    output = subprocess.check_output('/sbin/ifconfig')
    ips = []

    for line in output.split('\n'):
        match = inet_addr.search(line)
        if not match:
            continue
        ip = match.group(2)
        if ip.startswith('127.'):
            continue
        ips.append(ip)
    return ','.join(ips)

def send_mail(to_list, subject, message, files):
    import smtplib
    from email.mime.text import MIMEText
    from email import Encoders
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEBase import MIMEBase

    mail_host = "sh-out.intel.com"
    me = 'NoReplyAtAll@intel.com'

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ';'.join(to_list)

    msg.attach(MIMEText(message))

    for filename in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(filename, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                        % os.path.basename(filename))
        msg.attach(part)

    try:
        s = smtplib.SMTP()
        s.connect(mail_host)
        s.sendmail(me, to_list, msg.as_string())
        s.close()
        return True
    except Exception, e:
        print str(e)

def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_dist():
    return '-'.join(platform.dist()[:2])

def get_arch():
    return platform.architecture()[0]

def query_pkg_info(pkg):
    dist = platform.dist()[0].lower()
    if dist == 'ubuntu':
        cmd = "dpkg -s %s | grep Version | awk 'BEGIN{RS=\"\r\"}{printf $2}'"
    else:
        cmd = 'rpm -q --qf "%%{version}-%%{release}\n" %s'

    return subprocess.check_output(cmd % pkg, shell=True,
                                   stderr=subprocess.STDOUT)