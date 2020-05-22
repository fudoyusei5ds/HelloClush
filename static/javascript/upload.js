
// 点击文件, 开始上传
document.querySelector("#upload-button01").onclick = () => {
    let upload_result = document.querySelector("#upload-result")

    if(document.querySelector("#upload-input01").files.length > 0){
        let file = document.querySelector("#upload-input01").files[0]
        let reader = new FileReader();

        reader.onloadstart = () => {
            upload_result.textContent = "开始读取..."
        }
        reader.onloadend = () => {
            if (reader.error) {
                upload_result.textContent = "读取失败, 多次失败请直接用u盘"
            } else {
                upload_result.textContent = "读取成功, 开始上传..."
                // todo: 生成md5值
                let xhr = new XMLHttpRequest();
                xhr.open("post", "/upload?filename="+file.name)
                xhr.overrideMimeType("application/octet-stream");
                xhr.sendAsBinary(reader.result);
                xhr.onreadystatechange = () => {
                    if (xhr.readyState == 4) {
                        if (xhr.status == 200) {
                            upload_result.textContent = "上传成功"
                        }
                        else {
                            upload_result.textContent = "上传失败, " + xhr.responseText
                        }
                    }
                }
            }
        }
        reader.readAsBinaryString(file)
    }
    else{
        upload_result.textContent = "尚未选择文件"
    }
}

// 下载点击的按钮也放到这边, 反正类型是一样的
document.querySelector("#download-button").addEventListener("click", ()=> {
    // 跳转到下载页面
    window.location.href = "http://"+window.location.host+"/download"
})