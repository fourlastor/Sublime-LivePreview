import sublime, sublime_plugin
import os

class LivePreviewAPI(object):
    """Manages settings and shared API"""

    observed_files = []
    clients = []

    @classmethod
    def get_setting(cls, key):
        settings = {'web_host': 'localhost', 'web_port': 9090, 'ws_host': 'localhost', 'ws_port': 9091, 'open_observed_files': False}
        if key in settings.keys():
            return settings[key]
        return None

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
    def observe_file(cls, file_name):
        """Adds a file to the observation array so it fires the page reload on save."""
        file_name = file_name.__str__()
        if cls.get_setting('open_observed_files'):
            window = sublime.active_window()
            view = window.find_open_file(file_name)
            if view is None:
                window.open_file(file_name)
        if file_name not in LivePreviewAPI.observed_files:
            LivePreviewAPI.observed_files.append(file_name)

    @classmethod
    def path_to_url(cls, file_name):
        """Transforms an absolute path in an url managed by the web server"""
        folders = cls.get_folders()
        for folder in folders:
            if file_name.startswith(folders[folder]):
                return folder + file_name[len(folders[folder]):]

    @classmethod
    def url_to_path(cls, url):
        """Transforms an url managed by the web server in an absolute path"""
        folders = cls.get_folders()
        words = list(filter(None, url.split(os.sep)))
        if(words[0] in folders):
            path = folders[words[0]]
            for word in words[1:]:
                path = os.path.join(path, word)
            return path
        else:
            return None

    @classmethod
    def reload_page(cls, file_name):
        """Sends a reload command to the page, empties the observed_files list to regenerate dependencies"""
        if file_name in LivePreviewAPI.observed_files:
            # LivePreviewAPI.observed_files = []
            for client in LivePreviewAPI.clients:
                client.send_reload()

        
