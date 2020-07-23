from tornado.web import Application, StaticFileHandler
from ClusterShell.Task import Task, task_self
from ClusterShell.NodeSet import NodeSet

from .request_handler import MainHandler, HelpHandler
from .request_handler import UploadHandler
from .request_handler import CreateHandler
from .mainWebSocket import MainWebSocket

from .config import STATICDIR

class HelloWorldApp(Application):
    def __init__(self):
        self.nodes_list = {}
        # 注册路由
        handlers = [
            (r'/', MainHandler),
            (r'/static/(.*)', StaticFileHandler, {"path": STATICDIR}), 
            (r'/MainSocket', MainWebSocket),
            (r'/upload', UploadHandler),
            (r'/help', HelpHandler),
            (r'/create-command', CreateHandler),
        ]
        super(HelloWorldApp, self).__init__(handlers)