import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import logging
import socket
import threading
import json
from datetime import datetime

# HTTP Server Constants
HOST = 'localhost'
PORT = 3000

# Socket Server Constants
SOCKET_HOST = 'localhost'
SOCKET_PORT = 5000

BUFFER_SIZE = 1024
BASE_DIR = Path()

# HTTP Request Handler
class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse(self.path)
        match parsed_path.path:
            case '/':
                self.send_html('index.html')
            case '/message.html':
                self.send_html('message.html')
            case _ :
                file = BASE_DIR.joinpath(parsed_path.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_client.sendto(post_data, (SOCKET_HOST, SOCKET_PORT))
        socket_client.close()

        self.send_response(200)
        self.end_headers()



    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mimi_type, _ = mimetypes.guess_type(filename)
        if mimi_type:
            self.send_header('Content-type', mimi_type)
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


# Socket Server Thread
class SocketServerThread(threading.Thread):
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_server:
            socket_server.bind((SOCKET_HOST, SOCKET_PORT))
            while True:
                data, _ = socket_server.recvfrom(BUFFER_SIZE)
                self.data_recording(data)

    def data_recording(self, data):
        parsed_data = parse_qs(data.decode('utf-8'))
        username = parsed_data.get('username', [''])[0]
        message = parsed_data.get('message', [''])[0]

        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            with open('storage/data.json', 'r') as file:
                json_data = json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            json_data = {}

        json_data[current_date] = {'username': username, 'message': message}
        try:

            with open('storage/data.json', 'w') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
        except ValueError as err:
            logging.error(err)
        except OSError as err:
            logging.error(err)



# Start HTTP Server
def start_http_server():
    http_server = HTTPServer((HOST, PORT), RequestHandler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt :
        http_server.server_close()


# Start Socket Server
def start_socket_server():
    socket_server_thread = SocketServerThread()
    socket_server_thread.daemon = True
    socket_server_thread.start()


if __name__ == '__main__':

    start_socket_server()
    start_http_server()
