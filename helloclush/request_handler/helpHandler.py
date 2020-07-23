from tornado.web import RequestHandler

from ..config import STATICDIR

# 打开帮助页面
class HelpHandler(RequestHandler):
    def get(self):
        with open(STATICDIR + "help.html", "r") as f:
            self.write(f.read())