from ClusterShell.NodeSet import NodeSet

from .cmdJob import CmdJob
from ..clush_handler import JobEventHandler

class CopyJob(CmdJob):
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