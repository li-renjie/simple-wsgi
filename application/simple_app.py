
def application(environ, start_response):
    """A simple application function"""
    resp_body = b'Hello, world!\n'
    status = '200 OK'
    resp_headers = [
        ('Content-type', 'text/plain'),
        ('Content-Length', str(len(resp_body)))
    ]
    start_response(status, resp_headers)
    return [resp_body]


class Application:
    """A simple application Class."""

    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response

    def __call__(self, *args, **kwargs):
        pass


