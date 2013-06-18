import sublime, sublime_plugin, webbrowser

class PreviewCommand(sublime_plugin.TextCommand):
    def run(self, edit):
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
            chrome.open(fname)
