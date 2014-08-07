from twisted.web import proxy, http
from twisted.internet import reactor
from twisted.python import log
import sys
log.startLogging(sys.stdout)

from twisted.web.http import HTTPClient, Request, HTTPChannel
from twisted.web.proxy import ProxyClientFactory, ProxyRequest
import urlparse


class IPProxyRequest(ProxyRequest):

    def process(self):
        parsed = urlparse.urlparse(self.uri)
        protocol = parsed[0]
        host = parsed[1]
        port = self.ports[protocol]
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        rest = urlparse.urlunparse(('', '') + parsed[2:])
        if not rest:
            rest = rest + '/'
        class_ = self.protocols[protocol]
        headers = self.getAllHeaders().copy()
        if 'host' not in headers:
            headers['host'] = host
        self.content.seek(0, 0)
        s = self.content.read()
        clientFactory = class_(self.method, rest, self.clientproto, headers,
                               s, self)

        if "host1" in host or "host2" in host:
            print("CHANGE")
            #host = "ip1"
            host = "ip2" 

        self.reactor.connectTCP(host, port, clientFactory)


class IPProxy(HTTPChannel):
    requestFactory = IPProxyRequest


class IPProxyFactory(http.HTTPFactory):
    protocol = IPProxy


reactor.listenTCP(8088, IPProxyFactory())
#reactor.listenUnix("/tmp/ps", IPProxyFactory())
