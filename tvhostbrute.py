import time
from datetime import timedelta
from tornado import httputil, httpclient, gen, ioloop, queues
from tornado.httpclient import HTTPError
from difflib import SequenceMatcher
from argparse import ArgumentParser
import sys

concurrency = 20
# httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
xff_ip = "127.0.0.1"
xff_headers = {}
headers_for_xff = [
    "CACHE_INFO",
    "CF_CONNECTING_IP",
    "CLIENT_IP",
    "COMING_FROM",
    "CONNECT_VIA_IP",
    "FORWARDED-FOR-IP",
    "FORWARDED-FOR",
    "FORWARDED",
    "FORWARDED_FOR",
    "FORWARDED_FOR_IP",
    "HTTP-CLIENT-IP",
    "HTTP-FORWARDED-FOR-IP",
    "HTTP-FORWARDED-FOR",
    "HTTP-FORWARDED",
    "HTTP-PC-REMOTE-ADDR",
    "HTTP-PROXY-CONNECTION",
    "HTTP-VIA",
    "HTTP-X-FORWARDED-FOR-IP",
    "HTTP-X-FORWARDED-FOR",
    "HTTP-X-FORWARDED",
    "HTTP-X-IMFORWARDS",
    "HTTP-XROXY-CONNECTION",
    "PC_REMOTE_ADDR",
    "PRAGMA",
    "PROXY",
    "PROXY_AUTHORIZATION",
    "PROXY_CONNECTION",
    "REMOTE_ADDR",
    "VIA",
    "X-FORWARDED-FOR",
    "X-FORWARDED",
    "X-REAL-IP",
    "X_CLUSTER_CLIENT_IP",
    "X_COMING_FROM",
    "X_DELEGATE_REMOTE_HOST",
    "X_FORWARDED",
    "X_FORWARDED_FOR",
    "X_FORWARDED_FOR_IP",
    "X_IMFORWARDS",
    "X_LOCKING",
    "X_LOOKING",
    "X_REAL_IP",
    "XONNECTION",
    "XPROXY",
    "XROXY_CONNECTION",
    "ZCACHE_CONTROL"
]
for xh in headers_for_xff:
    xff_headers.update({xh: xff_ip})
httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=100, defaults=dict(
    validate_cert=False,
    # proxy_host="127.0.0.1",
    # proxy_port=8080
))

async_http = httpclient.AsyncHTTPClient()
sync_http = httpclient.HTTPClient()


@gen.coroutine
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def get_url(host):
    try:
        request = httpclient.HTTPRequest(
            url=url,
            headers={"Host": host},
            validate_cert=False,
            # proxy_host="127.0.0.1",
            # proxy_port=8080
        )
        response = sync_http.fetch(request)
        print('fetched host: %s' % host)
        return response.body
    except HTTPError as e:
        if e.code == 404:
            if verbose is True:
                print('%s response with 404.' % host)
            if len(e.response.body) > 0:
                return e.response.body
        elif e.code != 404:
            if verbose is True:
                print('Exception: %s %s' % (e, host))
            raise gen.Return(False)


@gen.coroutine
def vhost_found(vhost):
    global finded, finded_list
    text = "%s is found!" % vhost
    length = 0
    if verbose is False:
        sys.stdout.write("\r")
        length = 60 - len(text)
    # print("Virutal host %s is found!\n" % vhost)
    sys.stdout.write("{:s}{:>{}s}".format(text, "\n", length if length > 0 else 0))
    sys.stdout.flush()
    finded += 1
    finded_list.append(vhost)


@gen.coroutine
def progress_update(i):
    sys.stdout.write("\r")
    # the exact output you're looking for:
    sys.stdout.write("[%-50s] %.1f%%" % ('=' * int(i / 2), i))
    sys.stdout.flush()


@gen.coroutine
def get_vhosts(host):
    u = scheme+ip
    current_len = None
    response_content = None
    if method == 1:
        c_vhost = {"Host": host + "." + domain}
    else:
        c_vhost = {"Host": host}
    try:
        request = httpclient.HTTPRequest(url=u, headers=c_vhost)
        response = yield async_http.fetch(request)
        current_len = len(response.body)
        response_content = response.body
    except HTTPError as e:
        if e.code == 404:
            if verbose is True:
                print('%s - 404.' % host)
            current_len = len(e.response.body)
            response_content = e.response.body
        elif e.code == 302 or e.code == 301:
            print('%s - %s' % (host, e.code))
        else:
            if verbose is True:
                print('Exception: %s %s' % (e, u))
            raise gen.Return([])

    if current_len is not None and response_content is not None:
        if verbose:
            print("%s response: baselen - %s | nflen - %s | curr - %s" % (host, f_len, nf_len, current_len))
        if abs(current_len - f_len) >= 10 and abs(current_len - nf_len) >= 10:
            vhost_found(host)
            raise gen.Return([])
        diff_base = similar(response_content, f_response)
        if nf is True:
            diff_nf = similar(response_content, nf_response)
        if diff_base <= 0.8:
            if nf is True:
                if diff_nf <= 0.8:
                    vhost_found(host)
                    raise gen.Return([])
            else:
                vhost_found(host)
                raise gen.Return([])
        if verbose:
            print("%s not found" % host)
    raise gen.Return([])


@gen.coroutine
def main():
    q = queues.Queue()
    show_progress = True
    start = time.time()
    fetching, fetched = set(), set()

    @gen.coroutine
    def fetch_url():
        global percent
        current_host = yield q.get()
        try:
            if current_host in fetching:
                return
            # progress
            if show_progress and verbose is False:
                q_size = q.qsize()
                if q_size % 10:
                    percent_new = float((all_count - q_size) * 100) / all_count
                    if int(percent) < percent_new:
                        percent = percent_new
                        progress_update(percent)
            if verbose is True:
                print('fetching %s' % current_host)
            fetching.add(current_host)
            urls = yield get_vhosts(current_host)
            fetched.add(current_host)
        finally:
            q.task_done()

    @gen.coroutine
    def worker():
        while True:
            yield fetch_url()

    # Start workers, then wait for the work queue to be empty.
    for _ in range(concurrency):
        worker()
    if method == 1:
        for h in vhosts:
            q.put(h.strip())
    else:
        for z in zones:
            for h in vhosts:
                q.put(z.strip() + "." + h.strip())
    all_count = q.qsize()
    yield q.join()  # timeout=timedelta(seconds=300)
    assert fetching == fetched
    print('\r\nDone in %d seconds, fetched %s URLs.' % (
        time.time() - start, len(fetched)))
    progress_update(100)
    print("\nBrute successfully completed. Found %d virtual host" % finded)


if __name__ == '__main__':
    # base checks
    # get base response
    # parse arguments
    parser = ArgumentParser()
    parser.add_argument("ip", type=str, help="IP address to vhost brute")
    parser.add_argument("-s", "--scheme", type=str, default="http", help="Scheme for bruteforce. Default: http")
    parser.add_argument("-d", "--domain", type=str, help="Domain form brute method 1")
    parser.add_argument("-m", "--method", type=int, default=1, help="Method for bruteforce")
    parser.add_argument("-v", "--verbose", type=bool, default=False, help="Show verbose information")
    parser.add_argument("-b", "--base", type=str, help="Base domain for bruteforce. Default: www.domain")
    parser.add_argument("-n", "--nf", type=str, help="Not found domain")
    parser.add_argument("-f", "--vhost", type=file, default="vhosts.list", help="File with vhosts list for bruteforce. "
                                                                                "Default: vhosts.list")
    parser.add_argument("-z", "--zone", type=str, help="File with domain names for method 2. Default: zones.list")
    parser.add_argument("-x", "--xff", type=bool, help="Add XFF headers.")
    arguments = parser.parse_args()

    percent = 0
    ip = arguments.ip
    vhosts = arguments.vhost
    zones = arguments.zone
    method = arguments.method
    if method == 1:
        print(arguments.domain)
        if arguments.domain:
            domain = arguments.domain
        else:
            print("If you use bruteforce method 1 then --domain is required.")
            sys.exit(1)
    else:
        if not zones or not arguments.base:
            print("If you use bruteforce method 2 then --zone file and --base is required.")
            sys.exit(1)
    scheme = arguments.scheme + "://"
    url = scheme + ip
    verbose = arguments.verbose
    # hostname for not found request
    nf_host = arguments.nf if arguments.nf else "thiisnotrealvhost"
    # Real vhost. Important. Needed for valid vhost check for successful remove duplicates
    f_host = arguments.base if arguments.base else "www." + domain
    nf = False
    f_response = get_url(f_host)
    f_len = len(f_response)
    nf_response = get_url(nf_host)
    if nf_response:
        nf = True
        nf_len = len(nf_response)
    finded = 0
    finded_list = []

    import logging
    logging.basicConfig()
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
