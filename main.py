import tornado
from tornado.ioloop import IOLoop

from helloWorldApp import HelloWorldApp
from jobManager import JobManager

def main():
    app = HelloWorldApp()
    app.listen(8080)
    loop = IOLoop.current()
    JobManager.set_event_loop(loop)
    loop.start()

if __name__ == "__main__":
    main()