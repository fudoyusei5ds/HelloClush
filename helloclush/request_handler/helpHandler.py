from tornado.web import RequestHandler

# 打开帮助页面
class HelpHandler(RequestHandler):
    def get(self):
        with open("static/help.html", "r") as f:
            self.write(f.read())