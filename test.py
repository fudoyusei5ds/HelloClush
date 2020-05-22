from ClusterShell.Event import EventHandler
from ClusterShell.Task import Task
from tornado.iostream import PipeIOStream
from tornado.ioloop import IOLoop
from tornado.concurrent import Future
from os import pipe

(rfd, wfd) = pipe()
read_pipe_stream = PipeIOStream(rfd)
write_pipe_stream = PipeIOStream(wfd)

loop = IOLoop()

class MyEventHandler(EventHandler): 
    def ev_start(self, worker):
        loop.add_callback(write_pipe_stream.write, b"job has started")
    def ev_hub(self, worker, node, rc):
        loop.add_callback(write_pipe_stream.write, bytes("node {} has finished {}".format(node, rc)))
    def ev_close(self, worker, timedout):
        loop.add_callback(write_pipe_stream.write, b"all job has finished")




task1 = Task()
task2 = Task()

future = read_pipe_stream.read_bytes(1000, partial=True)
# loop.add_callback(printf, future)

task1.run("hostname", nodes="192.168.0.3", handler = MyEventHandler())
task2.run("echo helloworld", nodes="192.168.0.3", handler = MyEventHandler())
