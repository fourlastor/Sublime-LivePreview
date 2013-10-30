import http.server
import threading

from .api import LivePreviewAPI

from wsgiref.simple_server import make_server
from .ws4py.websocket import WebSocket
from .ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from .ws4py.server.wsgiutils import WebSocketWSGIApplication

class LivePreviewHTTPRequestHandler(http.server.BaseHTTPRequestHandler, LivePreviewAPI):
    """Manages http requests"""
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
    def do_GET(self):
        file_name = self.url_to_path(self.path)
        print("{path} is {file_name}".format(path=self.path, file_name=file_name))
        if file_name is None:
            self.send_error(404, "File not found: {path}".format(path=self.path))
            return
        try:
            self.observe_file(file_name)
            f = open(file_name)
            self.do_HEAD()
            self.wfile.write(f.read().encode())
            f.close()
            return
        except IOError:
            self.send_error(404, "File not found: {path}".format(path=self.path))
    def log_request(self,code='-',size='-'): pass
    def log_error(self,format,*args): pass
    def log_message(self,format,*args): pass
    def observe_file(self, file_name):
        file_name = file_name.__str__()
        window = sublime.active_window()
        view = window.find_open_file(file_name)
        if view is None:
            window.open_file(file_name)
        if file_name not in LivePreviewEvents.files:
            LivePreviewEvents.files.append(file_name)

class LivePreviewWebSocketHandler(WebSocket, LivePreviewAPI):
    """Class to manage communication with browser"""
    pass
        
class LivePreviewNamedThread(threading.Thread, LivePreviewAPI):
    """Starts a server with a given name"""

    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__

    @classmethod
    def get_thread(cls):
        threads = threading.enumerate()
        for thread in threads:
            if thread.name is cls.__name__ and thread.is_alive():
                return thread
        return None

class LivePreviewBrowserThread(LivePreviewNamedThread):
    """Manages the browser"""
    def __init__(self, host, port, url):
        super().__init__()
        self.host = host
        self.port = port
        self.url = url
        self.chrome = None
        try:
            self.chrome = webbrowser.get('chrome')
        except webbrowser.Error:
            try:
                self.chrome = webbrowser.get('google-chrome')
            except webbrowser.Error:
                pass
    def run(self):
        if None != self.chrome:
            self.chrome.open("http://{host}:{port}/{url}".format(host=self.host, port=self.port, url=self.url))
        else:
            sublime.error_message('You must have chrome/chromium installed for this plugin to work.')

class LivePreviewWebThread(LivePreviewNamedThread):
    """Manages a thread which runs the web server"""
    def __init__(self):
        super().__init__()
        host, port = "localhost", 9090
        httpd = http.server.HTTPServer((host, port), LivePreviewHTTPRequestHandler)
        self.httpd = httpd

    def run(self):
        print('starting server...')
        self.httpd.serve_forever()

    def stop(self):
        if isinstance(self.httpd, http.server.HTTPServer):
            self.httpd.shutdown()
            self.httpd.server_close()

class LivePreviewWSServerThread(LivePreviewNamedThread):
    """Manages the web socket"""
    def __init__(self):
        super().__init__()
        self.ws_server = make_server('', 9091, server_class=WSGIServer,
                     handler_class=WebSocketWSGIRequestHandler,
                     app=WebSocketWSGIApplication(handler_cls=LivePreviewWebSocketHandler))
        self.ws_server.initialize_websockets_manager()
        
    def run(self):
        self.ws_server.serve_forever()

    def stop(self):
        if isinstance(self.ws_server, http.server.HTTPServer):
            self.ws_server.shutdown()
            self.ws_server.server_close()