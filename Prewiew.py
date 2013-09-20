import sublime, sublime_plugin
import webbrowser
import http.server
import threading
import os

def get_folders():
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
                    loop = True
                    num = 0
                    while(loop):
                        num += 1
                        k = key + " " + str(num)
                        if k in dic:
                            if dic[k] is f:
                                loop = False
                                break
                        else:
                            dic[k] = f
                            loop = False
                            break
            else:
                dic[key] = f
    return dic

def path_to_url(filename):
    folders = get_folders()
    for folder in folders:
        if filename.startswith(folders[folder]):
            return folder + filename[len(folders[folder]):]

def url_to_path(url):
    folders = get_folders()
    words = list(filter(None, url.split(os.sep)))
    if(words[0] in folders):
        path = folders[words[0]]
        for word in words[1:]:
            path = os.path.join(path, word)
        return path
    else:
        return None

def get_web_thread():
    threads = threading.enumerate()
    for thread in threads:
        if thread.name is LivePreviewWebThread.__name__ and thread.is_alive():
            return thread
    return None

class LivePreviewEvents(sublime_plugin.EventListener):
    """Handles events"""
    httpd = None
    @classmethod
    def setHttpd(cls, httpd):
        cls.httpd = httpd

class LivePreviewStartCommand(sublime_plugin.TextCommand):
    """Launches the browser for the current file"""
    def run(self, edit):
        web_thread = get_web_thread()
        if web_thread is None:
            sublime.run_command('live_preview_start_server')
        host, port = "localhost", 9090
        url = path_to_url(self.view.file_name())
        livePreviewBrowserThread = LivePreviewBrowserThread(host, port, url)
        livePreviewBrowserThread.start()
        
class LivePreviewStartServerCommand(sublime_plugin.ApplicationCommand):
    """Starts the web server and the web socket server"""
    def run(self):
        host, port = "localhost", 9090
        httpd = http.server.HTTPServer((host, port), LivePreviewHTTPRequestHandler)
        livePreviewWebThread = LivePreviewWebThread(httpd)
        livePreviewWebThread.start()

class LivePreviewStopServerCommand(sublime_plugin.ApplicationCommand):
    """Stops the web server and the web socket server"""
    def run(self):
        web_thread = get_web_thread()
        if web_thread is not None:
            web_thread.stop()
            web_thread.join()

class LivePreviewHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Manages http requests"""
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
    def do_GET(self):
        try:
            path = url_to_path(self.path)
            f = open(path)
            self.do_HEAD()
            self.wfile.write(f.read().encode())
            f.close()
            return
        except IOError:
            self.send_error(404, "File not found: {path}".format(path=self.path))
    def log_request(self,code='-',size='-'): pass
    def log_error(self,format,*args): pass
    def log_message(self,format,*args): pass

class LivePreviewWebThread(threading.Thread):
    """Manages a thread which runs the web server"""
    def __init__(self, httpd):
        super(LivePreviewWebThread, self).__init__()
        self.httpd = httpd
        self.name = self.__class__.__name__

    def run(self):
        self.httpd.serve_forever()

    def stop(self):
        if isinstance(self.httpd, http.server.HTTPServer):
            self.httpd.shutdown()
            self.httpd.server_close()

class LivePreviewBrowserThread(threading.Thread):
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
        