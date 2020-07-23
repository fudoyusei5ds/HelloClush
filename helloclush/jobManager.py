from tornado.websocket import WebSocketHandler
from ClusterShell.NodeSet import NodeSet
import tornado

from .job import CmdJob, CopyJob, RCopyJob

class JobManager():
    ws: WebSocketHandler = None # 用来接收命令和返回结果的ws, 多页面唯一
    current_job: CmdJob = None # 当前正在执行的工作, 我们不用编号表示
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
    def choose_job(cls, index) -> CmdJob:  # 通过索引, 获取指定的job
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
        job = CmdJob(command, nodeset, index, timeout=timeout)
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
    def get_current_job(cls) -> CmdJob:
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