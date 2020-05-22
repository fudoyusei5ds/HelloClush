document.querySelector("#rcopy-button").addEventListener("click", () => {
    if(selectnode == ""){
        this.alert("尚未选择节点")
        return 
    }
    let srcname = document.querySelector("#rcopy-input").value 
    if(srcfile == ""){
        this.alert("没有输入文件名或目录名")
        return
    }
    let data = {
        "nodes": selectnode,
        "type": "newjob",
        "subtype": "rcopy",
        "src": srcname,
    }
    ws.send(JSON.stringify(data))
})