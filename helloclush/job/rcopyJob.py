from ClusterShell.NodeSet import NodeSet

from .cmdJob import CmdJob
from ..clush_handler import RCopyJobEventHandler

class RCopyJob(CmdJob):
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