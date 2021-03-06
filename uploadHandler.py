from tornado.web import RequestHandler
import os

class UploadHandler(RequestHandler):
    def post(self):
        filename = self.get_argument("filename", default="")
        if filename == "": # or os.path.exists("store/"+filename):
            self.set_status(400)
            self.write("文件名不存在")
        else:
            fd = os.open("store/"+filename, os.O_RDWR|os.O_CREAT)
            os.write(fd, self.request.body)
            os.close(fd)
            self.set_status(200)