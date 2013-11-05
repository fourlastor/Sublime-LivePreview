import sublime, sublime_plugin
import select
import os

# LivePreview Imports
from .api import LivePreviewAPI
from .server import *

class LivePreviewEvents(sublime_plugin.EventListener, LivePreviewAPI):
    """Handles events"""
    def on_post_save_async(self, view):
        """Fired asyncrhonously every time a file is saved, if the file is being observed, fires the page reloading."""
        file_name = view.file_name()
        if file_name in LivePreviewAPI.observed_files:
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
            livePreviewWebThread = LivePreviewWebThread()
            livePreviewWebThread.start()
        ws_thread = LivePreviewWSServerThread.get_thread()
        if ws_thread is None:
            livePreviewWSServerThread = LivePreviewWSServerThread()
            livePreviewWSServerThread.start()

class LivePreviewStopServerCommand(sublime_plugin.ApplicationCommand, LivePreviewAPI):
    """Stops the web server and the web socket server"""
    def run(self):
        web_thread = LivePreviewWebThread.get_thread()
        if web_thread is not None:
            web_thread.stop()
            web_thread.join()
            print('stopped web server')
        ws_thread = LivePreviewWSServerThread.get_thread()
        if ws_thread is not None:
            ws_thread.stop()
            ws_thread.join()
            print('stopped ws server')
        