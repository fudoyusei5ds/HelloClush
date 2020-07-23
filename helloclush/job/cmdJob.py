from ClusterShell.Task import Task
from ClusterShell.NodeSet import NodeSet

from ..clush_handler import JobEventHandler

class CmdJob():
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