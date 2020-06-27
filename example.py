
def run_application():
    """Run application with wsgiref."""
    from wsgiref.simple_server import make_server
    from application.simple_app import application

    server = make_server('0.0.0.0', 8888, application)
    server.handle_request()


def run_simple_application():
    """Run application with wsgiserver."""
    from wsgiserver.wsgi_server import WSGIServer
    from application.simple_app import application

    server = WSGIServer('0.0.0.0', 1234)
    server.set_app(application)
    server.run_server()


def run_flask_application():
    """Run Flask application with wsgiserver."""
    from wsgiserver.wsgi_server import WSGIServer
    from flask import Flask, request

    app = Flask(__name__)

    @app.route('/hello')
    def hello_world():
        return 'Hello, World!'

    @app.route('/post', methods=['GET', 'POST'])
    def post():
        if request.method == 'POST':
            # return str(request.json)
            return request.get_data(as_text=True)
        else:
            return ''

    server = WSGIServer('0.0.0.0', 1234)
    server.set_app(app)
    server.run_server()


if __name__ == '__main__':
    # run_application()
    # run_simple_application()
    run_flask_application()

