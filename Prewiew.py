import sublime, sublime_plugin
import webbrowser
import http.server
import threading
import os
import select
from .websocket import WebSocketServer

class LivePreviewAPI(object):
    """Manages settings and shared API"""
    def get_setting(self):
        pass
    def set_setting(self):
        pass

    @classmethod
    def get_folders(cls):
        """Get Open Directories in Sublime"""
        dic = {}
        # retrieve all Sublime windows
        windows = sublime.windows()
        for w in windows:
            # and retrieve all unique directory path
            fs = w.folders()
            for f in fs:
                key = f.split(os.path.sep)[-1]
                if key in dic:
                    if dic[key] is f:
                        continue
                    else:
                        num = 0
                        while(True):
                            num += 1
                            k = "{key} {num}".format(key=key,num=num)
                            if k in dic:
                                if dic[k] is f:
                                    break
                            else:
                                dic[k] = f
                                break
                else:
                    dic[key] = f
        return dic

    @classmethod
    def path_to_url(cls, file_name):
        folders = cls.get_folders()
        for folder in folders:
            if file_name.startswith(folders[folder]):
                return folder + file_name[len(folders[folder]):]

    @classmethod
    def url_to_path(cls, url):
        folders = cls.get_folders()
        words = list(filter(None, url.split(os.sep)))
        if(words[0] in folders):
            path = folders[words[0]]
            for word in words[1:]:
                path = os.path.join(path, word)
            return path
        else:
            return None
        

class LivePreviewEvents(sublime_plugin.EventListener, LivePreviewAPI):
    """Handles events"""
    files = []
    def on_post_save_async(self, view):
        file_name = view.file_name()
        if file_name in self.__class__.files:
            print("would have reloaded")
            # empy list to regenerate dependencies
            self.__class__.files = []
        else:
            print("would not have reloaded")

class LivePreviewStartCommand(sublime_plugin.TextCommand, LivePreviewAPI):
    """Launches the browser for the current file"""
    def run(self, edit):
        sublime.run_command('live_preview_start_server')
        host, port = "localhost", 9090
        url = self.path_to_url(self.view.file_name())
        livePreviewBrowserThread = LivePreviewBrowserThread(host, port, url)
        livePreviewBrowserThread.start()
        
class LivePreviewStartServerCommand(sublime_plugin.ApplicationCommand, LivePreviewAPI):
    """Starts the web server and the web socket server"""
    def run(self):
        web_thread = LivePreviewWebThread.get_thread()
        if web_thread is None:
            host, port = "localhost", 9090
            httpd = http.server.HTTPServer((host, port), LivePreviewHTTPRequestHandler)
            livePreviewWebThread = LivePreviewWebThread(httpd)
            livePreviewWebThread.start()

class LivePreviewStopServerCommand(sublime_plugin.ApplicationCommand, LivePreviewAPI):
    """Stops the web server and the web socket server"""
    def run(self):
        web_thread = LivePreviewWebThread.get_thread()
        if web_thread is not None:
            web_thread.stop()
            web_thread.join()
            print('stopped server')

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

class LivePreviewNamedThread(threading.Thread, LivePreviewAPI):
    """Starts a server with a given name"""

    def __init__(self):
        super(LivePreviewNamedThread, self).__init__()
        self.name = self.__class__.__name__

    @classmethod
    def get_thread(cls):
        threads = threading.enumerate()
        for thread in threads:
            if thread.name is cls.__name__ and thread.is_alive():
                return thread
        return None

class LivePreviewWebThread(LivePreviewNamedThread):
    """Manages a thread which runs the web server"""
    def __init__(self, httpd):
        super(LivePreviewWebThread, self).__init__()
        self.httpd = httpd

    def run(self):
        print('starting server...')
        self.httpd.serve_forever()

    def stop(self):
        if isinstance(self.httpd, http.server.HTTPServer):
            self.httpd.shutdown()
            self.httpd.server_close()

class LivePreviewBrowserThread(LivePreviewNamedThread):
    """Manages the browser"""
    def __init__(self, host, port, url):
        super(LivePreviewBrowserThread, self).__init__()
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
        
class LivePreviewWebSocket(WebSocketServer, LivePreviewAPI):
    """Web socket to communicate with the browser plugin"""
    def new_client(self):
        rlist = [self.client]
        while True:
            wlist = []
            # if there is something to send, add self.client to the wlist
            ins, outs, excepts = select.select(rlist, wlist, [], 1)

            if excepts:
                raise Exception("Socket Exception")

            if self.client in ins:
                pass

            if self.client in outs:
                pass

class LivePreviewWSServerThread(LivePreviewNamedThread):
    """Manages the web socket"""
    def __init__(self, ws_server):
        super(LivePreviewWebSocketThread, self).__init__()
        self.ws_server = ws_server
        
    def run(self):
        self.ws_server.start_server()