"""
Profile calls to HTTP
http://coreygoldberg.blogspot.com/2009/09/python-http-request-profiler.html
"""

import os, urllib
import sys


base = os.environ['EZACS__FINDIT_TESTS__PROFILE_REQUEST__BASE']
host = os.environ['EZACS__FINDIT_TESTS__PROFILE_REQUEST__HOST']
path = os.environ['EZACS__FINDIT_TESTS__PROFILE_REQUEST__PATH']

infile = open(sys.argv[1])


def profile(path):
    import time
    import httplib
    # select most accurate timer based on platform
    if sys.platform.startswith('win'):
        default_timer = time.clock
    else:
        default_timer = time.time

    # profiled http request
    conn = httplib.HTTPConnection(host)
    start = default_timer()
    conn.request('GET', path)
    request_time = default_timer()
    resp = conn.getresponse()
    response_time = default_timer()
    size = len(resp.read())
    conn.close()
    transfer_time = default_timer()

    # output
    print '%.5f request sent' % (request_time - start)
    print '%.5f response received' % (response_time - start)
    print '%.5f content transferred (%i bytes)' % ((transfer_time - start), size)

grabbed = 0

for n, row in enumerate(infile.readlines()):
    u = row.replace('\n', '')
    print u
    if n == '':
        continue
    if n <= 40:
        continue

    #grab = urllib.urlopen(base + u)
    grab = profile(path + u)
    grabbed += 1

    if grabbed == 20:
        break
    print '\n=====\n'
