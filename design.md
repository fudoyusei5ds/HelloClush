# 设计文档

通过创建websocket, 将用户在页面的操作当成消息传递给helloclush, helloclush对消息进行处理, 包装, 再把消息传递给clush. clush处理命名, 返回结果. helloclush再对结果进行包装, 通过websocket将结果返回页面. 

## 目录结构

因为整体应用在部署前后部署后的结构应该是一样的. 和普通的应用不同, 因此无需考虑普通应用的打包或者安装问题. 而且python也没有编译这一说

```sh
customizations/  # 用来放用户自定义的命令模块
helloclush/     # 主模块文件
    handler/    # get/post请求处理
    job/        # clush的task管理
    mainWebSocket.py    # 处理websocket请求
static/         # 静态资源, 包括css, js, 图片, html等
warehouse/      # 应用运行过程中用来保存数据的目录
    store/      # 上传, 下载功能实际上是和copy, rcopy相绑定的, 因此这四个操作都限定在这个目录下进行
    output/     # 节点的输出, 我们可以按照 节点ip:执行命令:种类:乱码 这样来命名文件. 方便我们日后检查
tests/          # 放测试用例, 每个测试用例名为 t_测试模块_编号.py 这样子的格式, 
readme.md
main            # 开始运行应用
run             # 启动用来测试的docker 
```