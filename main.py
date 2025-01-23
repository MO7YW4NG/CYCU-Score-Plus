import webview
import threading
import socket
from random import randint
from backend.app import start_server

def get_unused_port():
    while True:
        port = randint(1024, 65535)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port

def start_webview(port):
    webview.create_window("Score+", f"http://localhost:{port}/", resizable=False, width=1000, height=600)
    webview.start()

if __name__ == "__main__":
    port = get_unused_port()
    webview_thread = threading.Thread(target=start_server, args=('localhost', port))
    webview_thread.daemon = True
    webview_thread.start()
    
    start_webview(port)