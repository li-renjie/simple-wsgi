import socket
import sys
import os
from threading import Thread
from io import StringIO


class WSGIServer:
    """Start a socket server"""

    application = None
    _threads = []

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        # self.run_server()

    def run_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print('WSGIServer is listening at {}:{} ...'.format(self.host, self.port))

        while True:
            connection, client_addr = self.socket.accept()
            print('Receive a new connection, client addr {}'.format(client_addr))
            t = Thread(target=self.handle_connection, args=(connection, client_addr))
            t.setDaemon(True)
            self._threads.append(t)
            t.start()

    def handle_connection(self, connection, client_addr):
        RequestHandler(self.application, connection, client_addr)

    def set_app(self, application):
        self.application = application

    def get_app(self):
        return self.application

    def close(self):
        if self.socket:
            self.socket.close()


class RequestHandler:
    """Handle a request with WSGI."""

    def __init__(self, application, request, client_addr):
        self.request = request
        self.client_addr = client_addr
        self.application = application
        self.env = dict(os.environ.items())
        self.request_parser = None
        self.response_status = None
        self.response_headers = []
        self.response_headers_sent = False
        self.handle_request()

    def handle_request(self):
        request_raw_data = self.request.recv(65535)
        request_data = str(request_raw_data, 'iso-8859-1')     #

        for line in request_data.split('\r\n'):
            print(line)

        self.request_parser = HttpRequestParser(request_data)

        self.setup_environ()
        env = self.get_environ()
        #print(env)
        #print('socket info: {}'.format(dir(self.request)))

        result = self.application(self.env, self.start_response)
        self.finish_response()

    def setup_environ(self):
        """
        REF: https://www.python.org/dev/peps/pep-3333/#environ-variables
        """

        # WSGI-defined variables
        self.env['wsgi.version']      = (0, 1)
        self.env['wsgi.url_scheme']   = self.get_scheme()      # http or https
        self.env['wsgi.input']        = self.request.makefile(mode='rb')
        self.env['wsgi.errors']       = sys.stderr
        self.env['wsgi.multithread']  = True
        self.env['wsgi.multiprocess'] = False
        self.env['wsgi.run_once']     = False

        # CGI environment variables
        self.env['REQUEST_METHOD']    = self.request_parser.get_http_method()
        self.env['SCRIPT_NAME']       = ''
        self.env['PATH_INFO']         = self.request_parser.get_http_path()
        self.env['QUERY_STRING']      = self.request_parser.get_http_query_string()
        self.env['CONTENT_TYPE']      = self.request_parser.get_content_type()
        self.env['CONTENT_LENGTH']    = self.request_parser.get_content_length()
        self.env['SERVER_PROTOCOL']   = self.request_parser.get_http_version()
        self.env['SERVER_NAME']       = socket.getfqdn()
        self.env['SERVER_PORT']       = self.request.getsockname()[1]

        # CGI HTTP_ Variables

    def get_environ(self):
        return self.env

    def start_response(self, status, headers, exc_info=None):
        """start_response() callable as specified by PEP 3333
        status: HTTP "status" string like "200 OK" or "404 Not Found".
        headers: A list of (header_name, header_value) tuples.
        exc_info: If supplied, must be a Python sys.exc_info() tuple.
        """

        if exc_info:
            try:
                raise (exc_info[0], exc_info[1], exc_info[2])
            finally:
                exc_info = None  # Avoid circular ref.

        self.response_status = status
        self.response_headers = headers
        return self.write

    def write(self, data):
        """write() callable as specified by PEP 3333

        """

    def finish_response(self):
        self.send_headers()
        self.request.close()

    def send_headers(self):
        if self.response_headers_sent:
            return
        version = 'HTTP/1.1'
        status_line = '{} {}\r\n'.format(version, self.response_status)
        self.request.send(status_line.encode('iso-8859-1'))
        print(self.response_headers)
        self.response_headers_sent = True

    def get_scheme(self):
        if self.env.get('HTTPS') in ('yes', 'on', 1):
            return 'https'
        else:
            return 'http'


class HttpRequestParser:

    def __init__(self, request_data):
        self.method = None       # GET
        self.uri = None          # /abc?key=value
        self.version = None      # HTTP/1.1
        self.headers = {}
        self.request_body = None
        self.request_data = request_data
        self._parse_request()

    def _parse_request(self):
        request_line = self.request_data.splitlines()[0]
        self.method, self.uri, self.version = request_line.split()
        self._parse_headers()

    def _parse_headers(self):
        # header_lines = self.request_data.splitlines()[1]
        header_lines, self.request_body = self.request_data.split('\r\n\r\n')
        headers = header_lines.split('\r\n')[1:]
        for header in headers:
            name, value = header.split(': ')
            self.headers[name] = value

    def get_http_method(self):
        return self.method

    def get_http_path(self):
        return self.uri.split('?')[0]

    def get_http_query_string(self):
        if '?' in self.uri:
            return self.uri.split('?')[1]
        else:
            return ''

    def get_http_version(self):
        return self.version

    def get_http_headers(self):
        return self.headers

    def get_http_data(self):
        return self.request_body

    def get_content_type(self):
        return self.get_header('Content-Type')

    def get_content_length(self):
        return self.get_header('Content-Length')

    def get_header(self, header_name):
        if header_name in self.headers:
            return self.headers[header_name]
        else:
            return ''


if __name__ == '__main__':
    server = WSGIServer('0.0.0.0', 1234)
