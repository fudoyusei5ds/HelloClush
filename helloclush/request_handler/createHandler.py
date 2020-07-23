# 当用户创建新命令模块的时候使用

from tornado.web import RequestHandler
from ..config import CUSTOMDIR, STATICDIR

class CreateHandler(RequestHandler):
    def post(self):
        filename = self.get_argument("filename", default="")
        if filename == "": # or os.path.exists("store/"+filename):
            self.set_status(400)
            self.write("文件名不存在")
        else:
            with open(CUSTOMDIR+filename, "w") as f:
                f.write(self.request.body.decode())
            self.set_status(200)

    def get(self):
        with open(STATICDIR + "create.html", "r") as f:
            self.write(f.read())