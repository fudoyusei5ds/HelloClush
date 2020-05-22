from tornado.websocket import WebSocketHandler, WebSocketClosedError

from ClusterShell.Task import Task
from ClusterShell.Event import EventHandler
from ClusterShell.Worker.Ssh import WorkerSsh
from ClusterShell.NodeSet import NodeSet

import tornado

class Job():
    def __init__(
        self, 
        command: str, 
        nodeset: NodeSet, 
        index: int, 
        timeout: int=None,
    ):
        self.nodeset = nodeset  # 使用的节点组
        self.command = command  # 使用的命令
        self.state = 0          # 状态, 0等待运行, 1正在运行, 2运行成功, -1运行失败, -2自主中止
        self.scount = 0         # 成功的节点个数
        self.fcount = 0         # 失败的节点个数
        self.index = index      # 当前任务的编号
        self.timeout = timeout  # 暂时没用
        self.type = "cmd"       # 当前任务的性质
        self.task = Task()      # 在job创建时创建, 因为是在ws的线程上创建的, 所以属于ws的子线程

    def abort(self) -> int:
        # 我们只会在正在执行的任务上调用这个方法
        if self.state == 1 or self.state == 0:
            ret = self.state
            self.state = -2
            self.task.abort(kill=False)
            return ret
        return -1
    
    def restart(self) -> bool:
        # 已关闭或者已结束的任务，我们需要将其重新运行, 注意， 我们只能在没有运行的任务上运行重启指令(这不是多此一举, 而是为了使逻辑更合理). 
        # 因此, 即使前端设置了运行的任务上不会发送重启请求, 我们依然需要进行判断, 避免这种情况发生
        if self.state == 1 or self.state == 0:
            return False
        self.task.abort(kill=False) # 无论如何, 我们都要abort掉原来的线程, 因为我们马上就要创建一个新的线程. 这种方法虽然笨重, 但是足以面对各种情况
        self.task = Task()  # 正因为如此, 我们只能在ws线程上调用这个函数
        self.state = 0  # 我们只负责将任务设置到可以继续运行的状态
        # 同时将成功数和失败数清0
        self.scount = 0
        self.fcount = 0
        return True


    def execute(self) -> bool:
        # 假如任务正在执行, 那么我们直接退出
        if self.task.running():   # 在这里使用这种方式而不是state直接进行判断, 是因为我们担心state的判断条件会过于宽松, 造成不可知的风险
            return False
        else:
            self.task.shell(
                self.command,
                nodes = self.nodeset,
                handler=JobEventHandler(),
                timeout=self.timeout,
            )
            self.task.resume()
            self.state = 1
            return True
    

class CopyJob(Job):
    def __init__(
        self, 
        src: str,
        dest: str,
        nodeset: NodeSet,
        index: int,
        timeout: int=None,
    ):
        command = "cp {} {}".format(src, dest)
        super(CopyJob, self).__init__(command, nodeset, index, timeout=timeout)
        self.type = "copy"
        self.source = "store/" + src
        self.dest = dest

    def execute(self):
        if self.task.running():
            return False
        else:
            self.task.copy(  # 执行复制文件的操作
                self.source,
                self.dest,
                self.nodeset,
                handler=JobEventHandler(),
                timeout=self.timeout,
            )
            self.task.resume()
            self.state = 1
            return True

class RCopyJob(Job):
    def __init__(self, src: str, nodeset: NodeSet, index: int):
        command = "rcp {} {}".format(src, "/rcopy/")
        super(RCopyJob, self).__init__(command, nodeset, index, None)
        self.type = "rcopy"
        self.source = src
        self.dest = "rcopy/"
    def execute(self):
        if self.task.running():
            return False
        else:
            self.task.rcopy(
                self.source,
                self.dest,
                self.nodeset,
                handler = RCopyJobEventHandler(),
            )
            self.task.resume()
            self.state = 1
            return True


class JobManager():
    ws: WebSocketHandler = None # 用来接收命令和返回结果的ws, 多页面唯一
    current_job: Job = None # 当前正在执行的工作, 我们不用编号表示
    jobs: list = list()         # 用来保存任务, 同时也是优先级队列
    jobs_num: int = 0           # 当前的任务个数, 也是jobs列表的长度
    event_loop: tornado.ioloop.IOLoop = None
    max_index: int = -1 # 留用
    
    @classmethod
    def new_position(cls, new_pos) -> bool:
        # 我们传递过来的, 就是jobs的新的排列顺序. 首先我们要对这个排列顺序进行检测, 确保其是合法的
        new_pos = set(new_pos)
        if len(new_pos) != cls.jobs_num:  # 转换成set, 自动去重, 避免有重复的情况出现, 假如数量过少, 我们直接退出
            return False
        new_jobs = []
        for idx in new_pos:   
            try:
                idx = int(idx)
            except ValueError:  # 修改不合法, 我们直接忽略
                return False
            for job in cls.jobs:
                if job.index == idx:
                    new_jobs.append(job)
                    break
            # 假如, 原队列中未找到对应的索引, 我们就忽略他
        if len(new_jobs) != cls.jobs_num:
            return False
        cls.jobs == new_jobs
        return True
        
    @classmethod
    def current_state(cls) -> dict:
        if cls.jobs_num == 0:
            return {"type": "start"}
        r = {"type": "recover", "jobs": [], "jobs_num": cls.jobs_num}
        for i in range(cls.jobs_num):
            i_r = {
                "index": cls.jobs[i].index,
                "nodesnum": len(cls.jobs[i].nodeset),
                "cmd": cls.jobs[i].command,
                "state": cls.jobs[i].state,
                "scount": cls.jobs[i].scount,
                "fcount": cls.jobs[i].fcount,
            }
            r["jobs"].append(i_r)
        return r

    @classmethod
    def choose_job(cls, index) -> Job:  # 通过索引, 获取指定的job
        if index >=0 and index <= cls.max_index:
            for job in cls.jobs:
                if index == job.index:
                    return job
        return None

    @classmethod
    def set_event_loop(cls, loop):
        cls.event_loop = loop
    @classmethod
    def add_ws_callback(cls, msg):  # 添加到回调函数, 用于子线程
        cls.event_loop.add_callback(JobManager.write_ws, msg)

    @classmethod
    def ws_init(cls, ws: WebSocketHandler):
        cls.ws = ws # 始终使用新的ws
    
    @classmethod
    def add_job(cls, command: str, nodeset: NodeSet, timeout: int=None,):
        index = cls.max_index + 1
        job = Job(command, nodeset, index, timeout=timeout)
        cls.jobs.append(job)
        cls.jobs_num += 1   # 长度+1
        cls.max_index += 1  # 最大索引+1
        return index
    
    @classmethod
    def add_cpjob(cls, src: str, dest: str, nodeset: NodeSet, timeout: int=None,):
        index = cls.max_index + 1
        job = CopyJob(src, dest, nodeset, index, timeout=timeout)
        cls.jobs.append(job)
        cls.jobs_num += 1
        cls.max_index += 1 
        return index
    
    @classmethod
    def add_rcpjob(cls, src: str, nodeset: NodeSet):
        index = cls.max_index + 1
        job = RCopyJob(src, nodeset, index)
        cls.jobs.append(job)
        cls.jobs_num += 1
        cls.max_index += 1
        return index
    
    @classmethod
    def remove_job(cls, index) -> bool:
        for i in range(cls.jobs_num):
            if cls.jobs[i].index == index:
                if cls.jobs[i].state != 0 or cls.jobs[i].state != 1:
                    del cls.jobs[i]
                    cls.jobs_num -= 1
                    return True
                else:
                    return False
        return False
    
    @classmethod
    def run_next_job(cls) -> bool:
        # 在创建任务, 退出任务, 重启任务, 任务执行完毕时, 我们按照顺序查看是否可以执行正在等待的任务
        if cls.current_job == None: # 假如, 当前的任务为空, 也就意味着任务还没有开始执行, 此时我们直接执行第一个任务
            if cls.jobs_num > 0:
                cls.current_job = cls.jobs[0]
                cls.current_job.execute()
                return True
            else:
                return False
        if cls.current_job and cls.current_job.state != 1:  # 假如, 当前任务不为空, 并且当前的任务状态并不是正在执行
            for job in cls.jobs:
                if job.state == 0:
                    cls.current_job = job
                    cls.current_job.execute()
                    return True
            return False
        return False

    @classmethod
    def get_current_job(cls) -> Job:
        return cls.current_job
    
    @classmethod
    def get_length(cls) -> int:
        return cls.jobs_num
    
    @classmethod
    def write_ws(cls, message: dict):    # 写信息到网页, 我们使用一个dict来传递json数据
        if cls.ws:
            # 关于ws交流的命令的格式, 还需要更多的处理
            cls.ws.write_message(message)
    
    @classmethod
    def close_ws(cls, ws: WebSocketHandler):    # 我们不确定这两种是否可以进行比较, 等下可以验证以下
        if ws == cls.ws:
            cls.ws = None
        ws.close()

class JobEventHandler(EventHandler):
    def ev_start(self, worker):
        # JobManager.init_event_loop()    # 在task线程上创建event_loop, 没有必要了
        now_job = JobManager.get_current_job()
        msg = {
            "type": "nodeset",
            "msg": "start",
            "index": now_job.index,
        }
        # JobManager.write_ws(msg)
        JobManager.add_ws_callback(msg) # 将这则消息写入到消息循化中

    def ev_close(self, worker):
        # 将任务的状态设置好, 通知网页, 然后检查下一个任务可不可以执行
        now_job = JobManager.get_current_job()
        if now_job.state == -2: # job是否是自己主动退出的
            msg = {
                "type": "nodeset",
                "msg": "abort",
                "index": now_job.index,
            }
        else:
            if now_job.fcount != 0:
                now_job.state = -1
                msg = {
                    "type": "nodeset",
                    "msg": "failfinish",
                    "index": now_job.index,
                }
            else:
                now_job.state = 2
                msg = {
                    "type": "nodeset",
                    "msg": "succfinished",
                    "index": now_job.index,
                }
        # JobManager.write_ws(msg)
        JobManager.add_ws_callback(msg)
        JobManager.run_next_job()

    def ev_hup(self, worker, node, rc):
        # 每当有节点执行完毕的时候
        now_job = JobManager.get_current_job()
        if rc == 0:
            now_job.scount += 1
            msg = {
                "type": "nodeset",
                "msg": "success",
                "index": now_job.index,
                "count": now_job.scount,
            }
        else:
            now_job.fcount += 1
            msg = {
                "type": "nodeset",
                "msg": "failed",
                "index": now_job.index,
                "count": now_job.fcount,
            }
        # JobManager.write_ws(msg)
        JobManager.add_ws_callback(msg)

        # 保存io信息
        print("{}:{}".format(node, worker.current_msg))

import os, tarfile, shutil

class RCopyJobEventHandler(JobEventHandler):
    def ev_hup(self, worker, node, rc):
        # 每当有节点执行完毕的时候
        now_job = JobManager.get_current_job()
        if rc == 0:
            # 假如我们复制的是一个目录, 我们就要压缩这个目录
            node_dst_path = "{}/.{}".format(now_job.dest, node)
            if os.path.isdir(node_dst_path):
                tar = tarfile.open("{}/{}.{}.tar.gz".format(now_job.dest, os.path.basename(now_job.source), node), "w:gz")
                for root,_dir,files in os.walk(node_dst_path):
                    for file in files:
                        fullpath = os.path.join(root, file)
                        tar.add(fullpath)
                tar.close()
                # 压缩完毕之后, 删除原目录
                shutil.rmtree(node_dst_path)
            # 然后再发送成功的消息, 避免出偏差
            now_job.scount += 1
            msg = {
                "type": "nodeset",
                "msg": "success",
                "index": now_job.index,
                "count": now_job.scount,
            }
        else:
            now_job.fcount += 1
            msg = {
                "type": "nodeset",
                "msg": "failed",
                "index": now_job.index,
                "count": now_job.fcount,
            }
        # JobManager.write_ws(msg)
        JobManager.add_ws_callback(msg)

        # 保存io信息
        print("{}:{}".format(node, worker.current_msg))