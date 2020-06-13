import socket
from threading import Thread


class WSGIServer:
    """Start a socket server"""

    application = None
    _threads = []

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.run_server()

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
        self.request_parser = None
        self.handle_request()

    def handle_request(self):
        request_data = self.request.recv(65535)
        request_data = str(request_data, 'iso-8859-1')     #

        for line in request_data.split('\r\n'):
            print(line)

        self.request_parser = HttpRequestParser(request_data)

        env = self.get_environ()
        print(env)


    def get_environ(self):
        """
        :return: env
        REF: https://www.python.org/dev/peps/pep-3333/#environ-variables
        """

        env = {}

        # WSGI-defined variables
        env['wsgi.version']       = (0, 1)
        env['wsgi.url_scheme']    = 'http'      # http or https
        env['wsgi.input']         = ''
        env['wsgi.errors']        = ''
        env['wsgi.multithread']   = True
        env['wsgi.multiprocess']  = False
        env['wsgi.run_once']      = False

        # CGI environment variables
        env['REQUEST_METHOD']     = self.request_parser.get_http_method()
        env['SCRIPT_NAME']        = ''
        env['PATH_INFO']          = self.request_parser.get_http_path()
        env['QUERY_STRING']       = self.request_parser.get_http_query_string()
        env['CONTENT_TYPE']       = self.request_parser.get_content_type()
        env['CONTENT_LENGTH']     = self.request_parser.get_content_length()
        env['SERVER_NAME']        = ''     # socket.getfqdn(host)
        env['SERVER_PORT']        = ''
        env['SERVER_PROTOCOL']    = self.request_parser.get_http_version()

        return env

    def start_response(self, status, headers, exc_info=None):
        if exc_info:
            try:
                # do stuff w/exc_info here
                pass
            finally:
                exc_info = None  # Avoid circular ref.

    def write(self):
        pass

    def finish_response(self):
        pass


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
        # print(self.method, self.uri, self.version)
        self._parse_headers()

    def _parse_headers(self):
        # header_lines = self.request_data.splitlines()[1]
        header_lines, self.request_body = self.request_data.split('\r\n\r\n')
        headers = header_lines.split('\r\n')[1:]
        for header in headers:
            name, value = header.split(': ')
            print('name:{} value:{}'.format(name, value))
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

