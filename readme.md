# init状态

当前`hello clush`处于init状态. 

目前已经完成的功能以及其对应的里功能:

1. 节点模块:  
    可以上传节点配置文件, 自定义节点内容. (只有这一个配置文件会生效)

2. 功能模块:  
    初始设定了几个功能模块, 包括上传, 复制, 反复制功能. 此外, 还提供了一个简陋的自定义功能, 可以自己创建功能模块

3. 执行模块:  
    点击功能运行, 就会在这部分产生job, job会组成一个队列, 按顺序执行. 具备暂停, 重启, 关闭, 退出. 显示运行结果等功能. 