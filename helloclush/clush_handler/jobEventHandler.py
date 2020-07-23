from ClusterShell.Event import EventHandler
from ..jobManager import JobManager

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