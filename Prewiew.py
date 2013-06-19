import sublime, sublime_plugin
import webbrowser
import http.server

class PreviewHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
    def do_GET(self):
        try:
            f = open(self.path)
            self.do_HEAD()
            self.wfile.write(f.read().encode())
            f.close()
            return
        except IOError:
            self.send_error(404, "File not found: {path}".format(path=self.path))
    def log_request(self,code='-',size='-'): pass
    def log_error(self,format,*args): pass
    def log_message(self,format,*args): pass


class PreviewCommand(sublime_plugin.TextCommand):
    HOST, PORT = "localhost", 9090
    httpd = None

    def run(self, edit, action='start'):

        if action == 'kill':
            print("Killing server...")
            self.killServer()
            return

        sublime.set_timeout(self.spawnServer, 0)
        sublime.set_timeout(self.startBrowser, 0)
            

    def spawnServer(self):
        """Spawns a new server instance if needed."""
        if not isinstance(self.httpd, http.server.HTTPServer):
            self.view.set_status('PreviewStatus', "Previewing on http://{host}:{port}".format(host=self.HOST, port=self.PORT))
            self.httpd = http.server.HTTPServer((self.HOST, self.PORT), PreviewHandler)
            print("Would spawn a new server")
            sublime.set_timeout_async(self.startServer)
        else:
            print("Would reuse the server")

    def startServer(self):
        try:
            self.httpd.serve_forever()
        except Exception:
            pass

    def startBrowser(self):
        chrome = None
        try:
            chrome = webbrowser.get('chrome')
        except webbrowser.Error:
            try:
                chrome = webbrowser.get('google-chrome')
            except webbrowser.Error:
                pass
        fname = self.view.file_name()
        if None != fname and None != chrome:
            chrome.open("http://{host}:{port}{path}".format(host=self.HOST, port=self.PORT, path=fname))
        else:
            print("No broweser found")

    def killServer(self):
        if isinstance(self.httpd, http.server.HTTPServer):
            self.httpd.server_close()
            del self.httpd
            self.view.erase_status('PreviewStatus')
        else:
            print("Not an instance of HTTPServer")