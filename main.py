import tornado
from tornado.ioloop import IOLoop

from helloclush import HelloWorldApp
from helloclush import JobManager

def main():
    app = HelloWorldApp()
    app.listen(8080)
    loop = IOLoop.current()
    JobManager.set_event_loop(loop)
    loop.start()

if __name__ == "__main__":
    main()