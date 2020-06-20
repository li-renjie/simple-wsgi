
def application(environ, start_response):
    """A simple application function"""
    resp_body = b'Hello, world!\n'
    status = '200 OK'
    resp_headers = [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(resp_body)))
    ]
    start_response(status, resp_headers)
    return [resp_body]    # return an iterable


class Application:
    """A simple application Class.
    app = Application(environ, start_response)
    """

    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.resp_body = b'Hello, world!\n'
        self.status = '200 OK'
        self.resp_headers = [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(resp_body)))
        ]

    def __iter__(self):
        self.start_response(self.status, self.resp_headers)
        yield self.resp_body


class ApplicationCallable:
    """"""

    resp_body = b'Hello, world!\n'
    status = '200 OK'
    resp_headers = [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(resp_body)))
    ]

    def __call__(self, environ, start_response):
        start_response(self.status, self.resp_headers)
        return [self.resp_body]

