var aTag = document.getElementsByTagName('a')
var localURL = location.href
var arr1 = localURL.split('/')
var formatedURL = arr1[arr1.length-1]

function addActive(){
    if (formatedURL === 'stocks'){
        aTag[2].classList.add('active')
    }
    if (formatedURL === 'chart'){
        aTag[3].classList.add('active')
    }
}

function addLoadEvent(func){
    var oldLoad = onload
    if (typeof onload !== 'function'){
        onload = func
    }
    else {
        onload = function(){
            oldLoad()
            func()
        }
    }
}