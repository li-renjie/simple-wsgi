
def run_application():
    from wsgiref.simple_server import make_server
    from application.simple_app import application
    server = make_server('0.0.0.0', 8888, application)
    server.handle_request()


if __name__ == '__main__':
    run_application()

