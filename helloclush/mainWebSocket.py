from tornado.websocket import WebSocketHandler

from ClusterShell.Task import Task, task_self, task_wait
from ClusterShell.NodeSet import NodeSet
from ClusterShell.Worker.Ssh import WorkerSsh

from .jobManager import JobManager 

import json, os

class MainWebSocket(WebSocketHandler):
    def open(self):
        JobManager.write_ws({
            "type": "close"
        }) # 一个新的ws进来了, 我们通知旧的ws, 关闭自己
        JobManager.ws_init(self)
        # 然后执行恢复现场的代码
        JobManager.write_ws(
            JobManager.current_state()
        )
    
    def new_job(self, data: dict) -> bool:
        # 新建工作
        if "nodes" not in data or data["nodes"] not in self.application.nodes_list: # 如果没有指定节点, 或者指定的节点组不在我们要使用的节点组列表里面
            return False
        nodeset = self.application.nodes_list[data["nodes"]]
        if "cmd" in data:
            print("new job cmd in {}".format(nodeset))
            # 通用模板, 执行命令的代码
            if not data["cmd"]:
                return False
            command = data["cmd"]
            index = JobManager.add_job(command, nodeset)
            # 把相关的信息发送回网页, 让网页创建对应的节点
            JobManager.write_ws({
                "type": "new",
                "index": index,
                "nodesnum": len(nodeset),
                "cmd": command,
            })
        elif "subtype" in data and data["subtype"] == "rcopy":
            print("new job: rcopy")
            if not data["src"]:
                return False
            index = JobManager.add_rcpjob(data["src"], nodeset)
            command = "rcopy {} /rcopy/".format(data["src"])
            JobManager.write_ws({
                "type": "new",
                "index": index,
                "nodesum": len(nodeset),
                "cmd": command,
            })
        elif "src" in data and "dest" in data:
            print("new job copy")
            # 复制文件
            if (not data["src"]) or (not data["dest"]):
                return False
            # 如果文件不存在
            if not os.path.isfile("store/"+data["src"]):
                JobManager.write_ws({
                    "type": "error",
                    "msg": "错误, 文件不存在",
                })
                return False
            index = JobManager.add_cpjob(data["src"], data["dest"], nodeset)
            command = "cp {} {}".format(data["src"], data["dest"])
            JobManager.write_ws({
                "type": "new",
                "index": index,
                "nodesnum": len(nodeset),
                "cmd": command,
            })
        else:
            return False
        # 尝试执行任务
        JobManager.run_next_job()
    
    def abort_job(self, data) -> bool:
        # 退出正在执行的工作, 1. 获取指定的工作的索引. 2, 退出工作. 3, 如果成功, 向前端发送状态变化的消息. 4, 尝试执行下一个工作
        if "index" not in data:
            return False
        job_index = data["index"]
        print("abort job {}".format(job_index))
        try:
            job_index = int(job_index)  # 将数据转化为int
        except ValueError:
            return False

        # 指定的工作正在运行, 或者正在等待执行, 这个判断我们交给abort自己执行
        job = JobManager.choose_job(job_index)
        if not job:
            return False
        ret = job.abort()
        if ret >= 0:
            # 假如任务没有正在执行, 我们调用abort并不会触发close事件, 因此需要我们手动关闭
            if ret == 0:
                msg = {
                    "type": "nodeset",
                    "msg": "abort",
                    "index": job_index,
                }
                JobManager.write_ws(msg)
            return True
        else:
            return False


    def restart_job(self, data: dict) -> bool:
        if "index" not in data:
            return False
        job_index = data["index"]
        print("restart job {}".format(job_index))
        try:
            job_index = int(job_index)  # 将数据转化为int
        except ValueError:
            return False
        job = JobManager.choose_job(job_index)
        if not job:
            return False
        if job.restart():
            msg = {
                "type": "nodeset",  # todo, 这里要修改成
                "msg": "restart",
                "index": job_index,
            }
            JobManager.write_ws(msg)
            JobManager.run_next_job()
            return True
        else:
            return False


    def on_message(self, data: str):
        # 一共两种消息
        # 1. 执行命令, 我们直接执行
        # 2. 复制文件, 首先要上传文件到服务器, 然后将这个文件复制到选择的节点上
        data = json.loads(data)
        # 我们首先检查数据里有没有我们关心的内容
        if "type" not in data:
            return 
        if data["type"] == "newjob":
            self.new_job(data)
        elif data["type"] == "abortjob":
            self.abort_job(data)
        elif data["type"] == "restartjob":
            self.restart_job(data)
        elif data["type"] == "schedulejob":
            self.schedule_job(data)
        elif data["type"] == "removejob":
            self.remove_job(data)
        else:
            pass
            
    def on_close(self):
        JobManager.close_ws(self)

    def schedule_job(self, data):
        print(data)
        new_pos = data["new_position"]
        JobManager.new_position(new_pos)
    
    def remove_job(self, data):
        # 日志输出
        print(data)
        # 判断是否指定了索引
        if "index" in data:
            index = data["index"]
        else:
            return False
        # 尝试转化为int, 确保输入合法
        try:
            index = int(index)
        except ValueError:
            return False
        # 执行删除任务
        if JobManager.remove_job(index):
            # 删除成功, 返回信息
            msg = {
                "type": "nodeset",
                "msg": "remove",
                "index": index,
            }
            JobManager.write_ws(msg)
            return True
        else:
            # 删除失败, 我们什么也不做
            return False