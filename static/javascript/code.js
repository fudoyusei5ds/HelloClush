
// 一种格式化的字符串
var item_html = `
<div class="queue-item %s" id="job-%s">
    <div>任务编号: %s, 执行命令: %s</div>
    <div>节点数: <em class="node-num">%s</em>, 成功: <em class="succ-num">%s</em>, 失败: <em class="fail-num">%s</em></div>
    <div class="action-bar">%s</div>
</div>
`

var abort_action_html = '<input type="button" value="中止">' // 在执行或者等待时, 我们才可以执行中止操作
var restart_action_html = '<input type="button" value="重启"><input type="button" value="删除">' // 一个任务被中断, 执行完毕时, 我们可以使用重启
var state_list = ["state-abort", "state-fail", "state-wait", "state-run", "state-succ"]
var button_list = [restart_action_html, restart_action_html, abort_action_html, abort_action_html, restart_action_html]

function change_item_state(item_index, state_name) {
    document.querySelector("#job-"+item_index).classList.remove("state-wait", "state-fail", "state-succ", "state-abort", "state-run")
    document.querySelector("#job-"+item_index).classList.add(state_name)
    document.querySelector("#job-"+item_index+">.action-bar").innerHTML = button_list[state_list.indexOf(state_name)]
}

document.querySelector("#quebox").addEventListener("click", function(evt) {
    if (event.target.value == "中止") {
        let data = {
            "type": "abortjob",
            "index": event.target.parentNode.parentNode.id.split("-")[1]
        }
        ws.send(JSON.stringify(data))
    }
    else if (event.target.value == "重启") {
        let data = {
            "type": "restartjob",
            "index": event.target.parentNode.parentNode.id.split("-")[1]
        }
        ws.send(JSON.stringify(data))
    }
    else if (event.target.value == "删除") {
        let data = {
            "type": "removejob",
            "index": event.target.parentNode.parentNode.id.split("-")[1]
        }
        ws.send(JSON.stringify(data))
    }
})

ws.onmessage = (evt) => {
    console.log(evt.data)
    let data = JSON.parse(evt.data)
    switch(data.type){
        case "start":
            // 开始一个全新的状态
            break
        case "recover":
            let rc_node_html = ""
            for(let i=0; i< data.jobs_num; ++i) {
                rc_node_html += item_html.format(
                    state_list[data.jobs[i].state+2], data.jobs[i].index,
                    data.jobs[i].index, data.jobs[i].cmd,
                    data.jobs[i].nodesnum, data.jobs[i].scount, data.jobs[i].fcount,
                    button_list[data.jobs[i].state+2]
                )
            }
            document.querySelector("#quebox").innerHTML = rc_node_html
            break
        case "new":
            // 新建div节点
            document.querySelector("#quebox").innerHTML += item_html.format(
                "state-wait", data.index,
                data.index, data.cmd, 
                data.nodesnum, 0, 0,
                abort_action_html
            )
            break
        case "nodeset":
            // 任务执行时的对策
            switch(data.msg){
                // 节点执行成功或失败
                case "success":
                    document.querySelector("#job-"+data.index+">div>.succ-num").innerText = data.count
                    break
                case "failed":
                    document.querySelector("#job-"+data.index+">div>.fail-num").innerText = data.count
                    break
                // 节点开始执行
                case "start":
                    change_item_state(data.index, "state-run")
                    break
                case "failfinish":
                    change_item_state(data.index, "state-fail")
                    break
                case "succfinished":
                    change_item_state(data.index, "state-succ")
                    break
                case "abort": // 节点退出执行
                    change_item_state(data.index, "state-abort")
                    break
                case "restart": // 节点重启, 我们清空成功或者失败的节点数量, 同时设置状态为wait
                    document.querySelector("#job-"+data.index+">div>.succ-num").innerText = 0
                    document.querySelector("#job-"+data.index+">div>.fail-num").innerText = 0
                    change_item_state(data.index, "state-wait")
                    break
                case "remove":
                    document.querySelector("#quebox").removeChild(document.querySelector("#job-"+data.index))
                    break
            }
            break
        case "close":
            // 关闭ws, 因为有新的连接进来了, 我们直接删除整个页面
            self.close()
            document.querySelector("html").innerHTML="对不起, 你的页面已关闭, 因为有一个新的连接已被使用. 你可以重新刷新页面夺回控制权."
            break
        case "error":
            this.alert(data.msg)
            break
    }
}

document.querySelector("#nodebox").addEventListener("click", function(e) {
    // nodebox点击高亮事件
    let who = e.target
    if (who.getAttribute("class") == "nodeset") {
        let nodesets = document.querySelectorAll(".nodeset")
        for(let i=0; i<nodesets.length; ++i) {
            nodesets[i].classList.remove("selected")
        }
        who.classList.add("selected")
        selectnode = who.innerText.split("\n")[0]
    }
})

// 发送消息, 安装消息
document.querySelector("#apt-button").onclick = (evt) => {
    if(selectnode == ""){
        this.alert("尚未选择节点")
        return 
    }
    let package = document.querySelector("#apt-input").value
    if(package == ""){
        this.alert("没有输入包")
        return
    }
    let cmd = "apt-get install -y "+package
    let data = {
        "nodes": selectnode,
        "type": "newjob",
        "cmd": cmd 
    }
    ws.send(JSON.stringify(data))
}

// 执行复制操作
document.querySelector("#copy-button").onclick = (evt) => {
    if(selectnode == ""){
        this.alert("尚未选择节点")
        return 
    }
    let srcfile = document.querySelector("#src-input").value
    let destdir = document.querySelector("#dest-input").value
    if(srcfile == "" || destdir == ""){
        this.alert("没有输入文件名或目录名")
        return
    }
    let data = {
        "nodes": selectnode,
        "type": "newjob",
        "src": srcfile,
        "dest": destdir,
    }
    ws.send(JSON.stringify(data))
}

// 以下添加拖动元素的代码
var dragged;    // 被选中拖动的div
var hold_item;  // 占位用的div
var startY;     // 鼠标的起始纵轴坐标 
var dragY;      // 拖动元素的起始y轴坐标
var isdragged = false;  // 是否有元素被选中拖动

var index, sindex; // 标记当前元素的位置, 以及元素的起始位置
var length;     // 整个元素的长度

document.querySelector("#quebox").addEventListener("mousedown", (evt) => {
    let target = evt.target
    if (target.tagName.toLowerCase() == "input") {
        return
    }
    let current_target = evt.currentTarget
    while (target != current_target) {
        if (target.classList && target.classList.contains("queue-item") && !target.classList.contains("state-run") && !target.classList.contains("state-wait")) {
            // 我们要获取点击的div在整个列表里的位置
            // 要被拖动的元素不能正在运行或者等待运行, 这是为了防止在运行过程中产生错误
            length = current_target.childElementCount
            for (let i=0; i<length; ++i) {
                if (current_target.children[i] == target) {
                    index = i   // 记录起始的位置
                    sindex = i
                    break
                }
            }
            dragged = target    // 在鼠标按下之后, 选中item
            // 我们需要创建一个占位用的方框, 将其放到被选中的div的位置
            hold_item = document.createElement("div")
            hold_item.classList.add("hold-item")
            let y = dragged.offsetTop
            current_target.insertBefore(hold_item, dragged)
            document.querySelector("#quebox-copy").appendChild(dragged)
            // 获取div原本的位置
            dragged.style.top = (y-5) + "px"
            dragged.classList.add("dragged")

            // 记录鼠标的初始位置
            startY = evt.clientY
            dragY = dragged.offsetTop

            isdragged = true
            document.querySelector("#quebox-copy").style.zIndex = 1
            break
        }
        target = target.parentNode
    }
})
document.querySelector("#quebox-copy").addEventListener("mousemove", (evt) => {
    if (isdragged == false) {
        return
    }
    // 加一个限制, 避免无限变化
    if ((dragged.offsetTop - hold_item.offsetTop)/2 < hold_item.offsetHeight && (hold_item.offsetTop - dragged.offsetTop)/2 < hold_item.offsetHeight) {
        dragged.style.top = (evt.clientY - startY) + dragY + "px"
    }

    // 然后随着被选中组件的顺序改变, 占位的div也要变化
    // 分别判断被选中div和占位符的上一个节点和下一个节点的位置
    let prev = hold_item.previousElementSibling
    if (prev) {
        if ((prev.offsetTop - dragged.offsetTop)*2 > prev.offsetHeight) {
            --index
            document.querySelector("#quebox").insertBefore(hold_item, prev)
        }
    }
    let next = hold_item.nextElementSibling
    if (next) {
        if ((dragged.offsetTop - next.offsetTop)*2 > next.offsetHeight) {
            ++index
            let temp = hold_item.nextElementSibling.nextElementSibling
            if (temp) {
                document.querySelector("#quebox").insertBefore(hold_item, temp)
            }
            else {
                document.querySelector("#quebox").appendChild(hold_item)
            }
        }
    }
})
document.addEventListener("mouseup", (evt) => {
    if (isdragged == false) {
        return
    }
    isdragged = false
    document.querySelector("#quebox").insertBefore(dragged, hold_item)
    document.querySelector("#quebox").removeChild(hold_item)
    document.querySelector("#quebox-copy").style.zIndex = -1
    dragged.classList.remove("dragged")
    if (index != sindex) {
        // 我们直接将修改排列后的索引顺序传递给后台
        let children = document.querySelector("#quebox").children
        let position = []
        for (let i=0; i<children.length; ++i) {
            position.push(children[i].id.split("-")[1])
        }
        let data = {
            "type": "schedulejob",
            "new_position": position 
        }
        ws.send(JSON.stringify(data))
    }
})

document.querySelector("#add-param").onclick = () => {
    window.location.href = "http://"+window.location.host+"/create-command"
}