function setup(){
    var bar = document.getElementById("search")
    var display = document.getElementById("results")

    function after_timeout(){
        var value = bar.value
        if(! value)
            return
        
        window.history.replaceState(null, "", $SCRIPT_ROOT+"search?query="+value)

        var on_load = function(){
            var json = JSON.parse(this.responseText)
            results.innerHTML = ""
            json.forEach(function(v){
                var div = document.createElement("div")
                var code = tokenize(v, "code")
                div.setAttribute("class", "result")
                div.appendChild(code)
                display.appendChild(div)
            })
        }


        var req = new XMLHttpRequest()
        req.addEventListener("load", on_load)
        req.open("GET", $SCRIPT_ROOT+"search/api/"+value)
        req.send()


    }

    var timer = false
    function search_onkeydown(){
        if(timer){
            clearTimeout(timer)
        }
        timer = setTimeout(after_timeout, 100)

    }

    bar.addEventListener('keyup', search_onkeydown)


}
