from twitter.util import find_links, follow_redirects, expand_line
import contextlib
import BaseHTTPServer
import SocketServer
from threading import Thread
import functools


def test_find_links():
    assert find_links("nix") == ("nix", [])
    assert find_links("http://abc") == ("%s", ["http://abc"])
    assert find_links("t http://abc") == ("t %s", ["http://abc"])
    assert find_links("http://abc t") == ("%s t", ["http://abc"])
    assert find_links("1 http://a 2 http://b 3") == ("1 %s 2 %s 3", 
        ["http://a", "http://b"])
    assert find_links("%") == ("%%", [])
    assert find_links("(http://abc)") == ("(%s)", ["http://abc"])

from collections import namedtuple
Response = namedtuple('Response', 'path code headers')

@contextlib.contextmanager
def start_server(*resp):
    def url(port, path): 
        return 'http://localhost:%s%s' % (port, path)
    
    responses = list(reversed(resp))
    
    class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_HEAD(self):
            response = responses.pop()
            assert response.path == self.path
            self.send_response(response.code)
            for header, value in response.headers.iteritems():
                self.send_header(header, value)
            self.end_headers()
            
    httpd = SocketServer.TCPServer(("", 0), MyHandler)
    t = Thread(target=httpd.serve_forever)
    t.setDaemon(True)
    t.start()
    port = httpd.server_address[1]
    yield functools.partial(url, port)
    httpd.shutdown()
    
def test_follow_redirects_direct_link():
    link = "/resource"
    with start_server(Response(link, 200, {})) as url:
        assert url(link) == follow_redirects(url(link))

def test_follow_redirects_redirected_link():
    redirected = "/redirected"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": redirected}), 
        Response(redirected, 200, {})) as url:
        assert url(redirected) == follow_redirects(url(link))
        
def test_follow_redirects_unavailable():
    link = "/resource"
    with start_server(Response(link, 404, {})) as url:
        assert url(link) == follow_redirects(url(link))

def test_follow_redirects_link_to_last_unavailable():
    unavailable = "/unavailable"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": unavailable}), 
        Response(unavailable, 404, {})) as url:
        assert url(unavailable) == follow_redirects(url(link))


def test_follow_redirects_no_where():
    link = "http://links.nowhere/"
    assert link == follow_redirects(link)
    
def test_follow_redirects_link_to_nowhere():
    unavailable = "http://links.nowhere/"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": unavailable})) as url:
        assert unavailable == follow_redirects(url(link))


def test_expand_line():
    redirected = "/redirected"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": redirected}), 
        Response(redirected, 200, {})) as url:
        fmt = "before %s after"
        line = fmt % url(link)
        expected = fmt % url(redirected)
        assert expected == expand_line(line)

