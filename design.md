# 设计文档

通过创建websocket, 将用户在页面的操作当成消息传递给helloclush, helloclush对消息进行处理, 包装, 再把消息传递给clush. clush处理命名, 返回结果. helloclush再对结果进行包装, 通过websocket将结果返回页面. 

