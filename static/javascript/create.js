String.prototype.format= function(){
    //将arguments转化为数组（ES5中并非严格的数组）
    var args = Array.prototype.slice.call(arguments);
    var count=0;
    //通过正则替换%s
    return this.replace(/%s/g,function(s,i){
        return args[count++];
    });
}

var param_index = 0
document.querySelector("#addparam-1").onclick = () => { // 添加普通参数
    let input_box = document.querySelector("#inputbox")
    input_box.innerHTML += `
    <div class="param-item">
        <input type="text" placeholder="参数名" class="param-main">
        <input type="text" placeholder="参数的描述" class="param-desc">
        <input type="button" value="删除" class="param-rm">  
    </div> 
    `
    param_index += 1
}
document.querySelector("#addparam-2").onclick = () => { // 添加隐藏参数
    let input_box = document.querySelector("#inputbox")
    input_box.innerHTML += `
    <div class="hide-item">
        <input type="text" placeholder="参数名" class="param-main">
        <input type="button" value="删除" class="param-rm">  
    </div> 
    `
    param_index += 1
}
document.querySelector("#inputbox").addEventListener("click", (evt) => {    // 删除
    let target = evt.target
    if(target.className == "param-rm") {
        let item = target.parentElement
        document.querySelector("#inputbox").removeChild(item)
        param_index -= 1 
    }
})

// 以下为保存内容, 将内容保存为一个html, 包括脚本, 然后上传到一个特定的目录. 每次主页刷新, 都会从这个目录读取.
document.querySelector("#save").onclick = () => {
    let cmd_name = document.querySelector("#input-1").value
    let cmd_desc = document.querySelector("#input-2").value
    let params = []
    let item_list = document.querySelectorAll("#inputbox>div")
    let cmd_line = cmd_name
    let cmd_div = ""
    for (let i=0; i<param_index; ++i) {
        if (item_list[i].className == "param-item") {
            cmd_line += "null,"
            let param_name = item_list[i].firstChild.value
            let param_desc = item_list[i].lastChild.value
            cmd_div += '<p>%s:<input type="text" placeholder="%s" class="param-input"></p>'.format(param_name, param_desc)
        }
        else if (item_list[i].className == "hide-item") {
            let param_name = item_list[i].firstChild.value
            cmd_line += "'" + param_name + "',"
        }
        params.push([param_name, param_desc])
    }
    // 应该生成一串随机数作为id
    let random_id = "cmd"+Math.floor(Math.random()*1000000000000000)
    let div_str = `
    <div id="%s-box">
        <p>%s</p>
        %s
        <p><input type="button" value="执行" id="%s-button"></p>
    </div>
    <script>
        // 直接反映, 应该没有问题
        document.querySelector("#%s-button").onclick = (evt) => {
            let cmd_list = ["%s"]  // 命令数组, 未命令的参数数量和input的个数是一样的
            if(selectnode == ""){
                this.alert("尚未选择节点")
                return 
            }
            // 点击发送按钮, 把命令发送到他该去的地方
            // 哈哈哈哈哈哈哈哈哈哈哈哈
            let input_list = document.querySelectorAll("#%s-box>p>.param-input")
            let index = 0
            for (let i=0; i<%s; ++i) {
                if (cmd_list[i] == null) {
                    if (input_list[index].value) {
                        cmd_list[i] = input_list[index].value
                        index += 1
                    }
                    else {
                        alert("参数不能为空")
                        return 
                    }
                }
            }
            let cmd = cmd_list.reduce((a, b) => { return a+" "+b })
            let data = {
                "nodes": selectnode,
                "type": "newjob",
                "cmd": cmd 
            }
            ws.send(JSON.stringify(data))
        }
    </script>
    `.format(random_id, cmd_desc, cmd_div, random_id, random_id, cmd_line, random_id, param_index)
    // 发送数据, ajax提交
    let upload_result = document.querySelector("#upload-result")
    let xhr = new XMLHttpRequest()
    xhr.open("post", "/create-command?filename="+random_id)
    xhr.overrideMimeType("application/octet-stream")
    xhr.send(div_str)
    upload_result.textContent = "开始保存..."
    xhr.onreadystatechange = () => {
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                upload_result.textContent = "保存成功, 请刷新主页应用更改."
                window.location.href = "http://"+window.location.host
            }
            else {
                upload_result.textContent = "保存失败, 请重新保存"
            }
        }
    }
}