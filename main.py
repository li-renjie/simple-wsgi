
def run_application():
    from wsgiref.simple_server import make_server
    from application.simple_app import application
    server = make_server('0.0.0.0', 8888, application)
    server.handle_request()


def run_simple_application():
    from wsgiserver.wsgi_server import WSGIServer
    from application.simple_app import application
    server = WSGIServer('0.0.0.0', 1234)
    server.set_app(application)
    server.run_server()


if __name__ == '__main__':
    # run_application()
    run_simple_application()

