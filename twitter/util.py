"""
Internal utility functions.

`htmlentitydecode` came from here:
    http://wiki.python.org/moin/EscapingHtml
"""

from __future__ import print_function

import re
import sys
import time
import urllib2
import contextlib

try:
    from html.entities import name2codepoint
    unichr = chr
except ImportError:
    from htmlentitydefs import name2codepoint

def htmlentitydecode(s):
    return re.sub(
        '&(%s);' % '|'.join(name2codepoint),
        lambda m: unichr(name2codepoint[m.group(1)]), s)

def smrt_input(globals_, locals_, ps1=">>> ", ps2="... "):
    inputs = []
    while True:
        if inputs:
            prompt = ps2
        else:
            prompt = ps1
        inputs.append(input(prompt))
        try:
            ret = eval('\n'.join(inputs), globals_, locals_)
            if ret:
                print(str(ret))
            return
        except SyntaxError:
            pass

def printNicely(string):
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout.buffer.write(string.encode('utf8'))
        print()
    else:
        print(string.encode('utf8'))

__all__ = ["htmlentitydecode", "smrt_input"]

def err(msg=""):
    print(msg, file=sys.stderr)

class Fail(object):
    """A class to count fails during a repetitive task.

    Args:
        maximum: An integer for the maximum of fails to allow.
        exit: An integer for the exit code when maximum of fail is reached.

    Methods:
        count: Count a fail, exit when maximum of fails is reached.
        wait: Same as count but also sleep for a given time in seconds.
    """
    def __init__(self, maximum=10, exit=1):
        self.i = maximum
        self.exit = exit

    def count(self):
        self.i -= 1
        if self.i == 0:
            err("Too many consecutive fails, exiting.")
            raise SystemExit(self.exit)

    def wait(self, delay=0):
        self.count()
        if delay > 0:
            time.sleep(delay)


def find_links(line):
    l = line.replace(u"%", u"%%")
    regex = "(https?://[^ )]+)"
    return (
        re.sub(regex, "%s", l), 
        [m.group(1) for m in re.finditer(regex, l)])
    
def expand_link(link):
    try:
        with contextlib.closing(urllib2.urlopen(link)) as site:
            return site.url
    except (urllib2.HTTPError, urllib2.URLError):
        return link

def expand_line(line):
    l = line.strip()
    msg_format, links = find_links(l)
    args = tuple(expand_link(l) for l in links)
    return msg_format % args
