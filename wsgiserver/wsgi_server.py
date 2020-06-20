import socket
import sys
import os
from threading import Thread
from io import BytesIO
from datetime import datetime


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
        print('WSGIServer is listening at {}:{}...'.format(self.host, self.port))

        while True:
            connection, client_addr = self.socket.accept()
            print('Receive a new connection, client: {}'.format(client_addr))
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
        self.request_body_bytes = None
        self.request_parser = None
        self.response_status = None
        self.response_headers = []
        self.response_data = None
        self.response_headers_sent = False
        self.handle_request()

    def handle_request(self):
        request_raw_data = self.request.recv(65535)

        # setup WSGI wsgi.input variable
        splitted_data = request_raw_data.split(b'\r\n\r\n')
        if len(splitted_data) >= 1:
            self.request_body_bytes =

        request_data = str(request_raw_data, 'iso-8859-1')     #
        self.request_parser = HttpRequestParser(request_data)

        for line in request_data.split('\r\n'):
            print(line)

        self.setup_environ()
        self.response_data = self.application(self.env, self.start_response)
        self.finish_response()

    def setup_environ(self):
        """ Setup WSGI-defined variables and CGI environment variables.

        REF: https://www.python.org/dev/peps/pep-3333/#environ-variables

        """

        # WSGI-defined variables
        self.env['wsgi.version']      = (1, 0)      # WSGI version 1.0
        self.env['wsgi.url_scheme']   = 'http'      # http or https
        # self.env['wsgi.input']        = self.request.makefile(mode='rb')
        # self.env['wsgi.input']        = BytesIO(self.request_data)
        self.env['wsgi.input']        = BytesIO(
            self.request_parser.get_request_body().encode('iso-8859-1')
        )
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

        # CGI HTTP_* Variables
        headers = self.request_parser.get_http_headers()
        for name, value in headers.items():
            name = name.upper().replace('-', '_')
            value = value.strip()
            env_name = 'HTTP_' + name
            self.env[env_name] = value

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

        New WSGI applications and frameworks should not use the write()
        callable if it is possible to avoid doing so. The write() callable
        is strictly a hack to support imperative streaming APIs.

        """
        if type(data) is not bytes:
            raise TypeError('write(data): data must be bytes.')

        if not self.response_headers_sent:
            raise AssertionError('write() before start_response()')

        self.request.sendall(data)

    def finish_response(self):
        self.send_headers()

        for data in self.response_data:
            print(data)
            self.write(data)       # self.request.send(data)
        self.request.close()

    def send_headers(self):
        if self.response_headers_sent:
            return

        # send response status line
        version = 'HTTP/1.1'
        status_line = '{} {}\r\n'.format(version, self.response_status)
        self.request.sendall(status_line.encode('iso-8859-1'))

        # send response headers
        if 'Date' not in self.response_headers:
            dt = datetime.utcnow()
            time_str = dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
            self.request.send('Date: {}\r\n'.format(time_str).encode('iso-8859-1'))
        for name, value in self.response_headers:
            header_line = '{}: {}\r\n'.format(name, value)
            self.request.sendall(header_line.encode('iso-8859-1'))
        self.request.sendall('\r\n'.encode('iso-8859-1'))

        self.response_headers_sent = True


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
        header_lines, self.request_body = self.request_data.split('\r\n\r\n')
        headers = header_lines.split('\r\n')[1:]
        for header in headers:
            name, value = header.split(': ')
            if name in self.headers:
                self.headers[name] = self.headers[name] + ',' + value
            else:
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

    def get_request_body(self):
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
