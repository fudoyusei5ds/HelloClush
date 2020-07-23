from tornado.web import Application, StaticFileHandler
from ClusterShell.Task import Task, task_self
from ClusterShell.NodeSet import NodeSet

from mainHandler import MainHandler, HelpHandler
from mainWebSocket import MainWebSocket
from uploadHandler import UploadHandler
from createHandler import CreateHandler

class HelloWorldApp(Application):
    def __init__(self):
        self.nodes_list = {}
        # 注册路由
        handlers = [
            (r'/', MainHandler),
            (r'/static/(.*)', StaticFileHandler, {"path": "./static"}), 
            (r'/MainSocket', MainWebSocket),
            (r'/upload', UploadHandler),
            (r'/help', HelpHandler),
            (r'/create-command', CreateHandler),
        ]
        super(HelloWorldApp, self).__init__(handlers)