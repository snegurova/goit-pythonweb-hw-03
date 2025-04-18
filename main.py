import json
import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse
from jinja2 import Environment, FileSystemLoader, select_autoescape


BASE_DIR = pathlib.Path()
DATA_FILE = BASE_DIR / 'storage' / 'data.json'
TEMPLATES_DIR = BASE_DIR / 'templates'
PORT = 3000


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path).path

        if route == '/':
            self.render_template('index.html')
        elif route == '/message':
            self.render_template('message.html')
        elif route == '/read':
            self.render_messages()
        elif route.startswith('/static/'):
            self.serve_static(route)
        else:
            self.send_error_page()

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode()
            data = urllib.parse.parse_qs(body)

            username = data.get('username', ['Anonymous'])[0]
            message = data.get('message', [''])[0]

            timestamp = str(datetime.now())

            if DATA_FILE.exists():
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            else:
                messages = {}

            messages[timestamp] = {'username': username, 'message': message}

            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)

            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_error_page()

    def render_template(self, filename):
        filepath = TEMPLATES_DIR / filename
        if filepath.exists():
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(filepath.read_bytes())
        else:
            self.send_error_page()

    def render_messages(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        except FileNotFoundError:
            messages = {}

        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html", "xml"])
        )
        template = env.get_template("read.html")
        rendered_page = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(rendered_page.encode("utf-8"))

    def serve_static(self, route):
        filepath = BASE_DIR / route[1:]
        if filepath.exists():
            self.send_response(200)
            mime_type, _ = mimetypes.guess_type(str(filepath))
            self.send_header('Content-Type', mime_type or 'application/octet-stream')
            self.end_headers()
            self.wfile.write(filepath.read_bytes())
        else:
            self.send_error_page()

    def send_error_page(self):
        filepath = TEMPLATES_DIR / 'error.html'
        self.send_response(404)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        if filepath.exists():
            self.wfile.write(filepath.read_bytes())
        else:
            self.wfile.write(b'<h1>404 Not Found</h1>')


def run():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f'Server running on port {PORT}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
