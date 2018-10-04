//得到button元素
var btn = document.getElementsByClassName('btn')[0]
var inner_text = btn.innerText
var info_el = document.getElementById('coin_info')
function toggle(){
        console.log('ok')
        if(inner_text == '+'){
            inner_text = '-';
            info_el.style.display = 'block'
        }
        else if (){
            inner_text = '+';
            info.style.display = 'none'
    }
}