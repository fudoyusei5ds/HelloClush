
import random
import threading
import time

import tornado.ioloop
import tornado.locks

loop = tornado.ioloop.IOLoop()

condition = tornado.locks.Condition()

async def respond_to_event(condition, who_am_i):
    while True:
        await condition.wait()  # awake when the event is triggered
        print(who_am_i, 'triggered on thread', threading.get_ident()) # 当子线程释放了cond, 这边主线程就被唤醒了, 然后打印这个. 因为添加了三个, 所以三个都要执行

print("main thread {}".format(threading.get_ident()))
loop.add_callback(respond_to_event, condition, 'one')
loop.add_callback(respond_to_event, condition, 'two')
loop.add_callback(respond_to_event, condition, 'three')


def my_separate_thread():
    time.sleep(1)
    print('triggering on thread', threading.get_ident())    # 在子线程上打印这个
    loop.add_callback(condition.notify_all)  # 然后调用add_callback, 把释放cond的函数添加到下一个事件循环

    time.sleep(1)
    print('\ntriggering on thread', threading.get_ident())
    loop.add_callback(condition.notify_all)

    time.sleep(1)
    print('\ntriggering on thread', threading.get_ident())
    loop.add_callback(condition.notify_all)

    time.sleep(1)
    loop.add_callback(loop.stop)

thread = threading.Thread(target=my_separate_thread, daemon=False)
thread.start()  # start thread in the background

loop.start()
