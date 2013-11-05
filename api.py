import sublime, sublime_plugin

class LivePreviewAPI(object):
    """Manages settings and shared API"""

    clients = []

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