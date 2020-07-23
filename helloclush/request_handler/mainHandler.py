# 主页面, 用户访问网站的时候使用

from tornado.web import RequestHandler
from ClusterShell.NodeSet import NodeSet
import os

from ..config import GROUPS_CONFIG, STATICDIR, CUSTOMDIR

# 主页面
class MainHandler(RequestHandler):
    def get(self):
        nodes_list = {}
        if os.path.isfile(GROUPS_CONFIG):
            with open(GROUPS_CONFIG, "r") as f:
                for l in f:
                    if ":" in l:
                        l = l.strip().split(":",1)
                        nodes_list[l[0]] = NodeSet(l[1])
        else:
            nodes_list = {}
        self.application.nodes_list = nodes_list
        
        # 添加读取组的配置文件, 然后写入到网页中
        with open(STATICDIR + "index.html", "r") as f:
            self.write(f.read().format(self.build_html(nodes_list), self.get_extent()))

    def get_extent(self) -> str:
        s = ""
        for f in os.listdir(CUSTOMDIR):
            with open(CUSTOMDIR+f, "r") as r:
                s += r.read()
        return s

    def build_html(self, nodes_list: dict) -> str:
        if nodes_list == {}:
            return ""
        html = ""
        for key in nodes_list:
            item = '<div class="nodeset">' + key + '<br>' + str(nodes_list[key]) + '</div>'
            html += item
        return html

