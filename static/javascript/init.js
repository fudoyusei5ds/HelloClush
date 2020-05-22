String.prototype.format= function(){
    //将arguments转化为数组（ES5中并非严格的数组）
    var args = Array.prototype.slice.call(arguments);
    var count=0;
    //通过正则替换%s
    return this.replace(/%s/g,function(s,i){
        return args[count++];
    });
}

// 将读取的文件当作二进制发送到主机上
XMLHttpRequest.prototype.sendAsBinary = function(datastr) {
    function byteValue(x) {
        return x.charCodeAt(0) & 0xff;
    }
    var ords = Array.prototype.map.call(datastr, byteValue);
    var ui8a = new Uint8Array(ords);
    this.send(ui8a.buffer);
}

var selectnode = ""

var ws = new this.WebSocket("ws://"+window.location.host+"/MainSocket")