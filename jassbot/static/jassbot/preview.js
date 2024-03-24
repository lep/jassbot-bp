function setup(){
    const bar = document.getElementById("search")
    const display = document.getElementById("result")
    const results = display.querySelector('.results')
    const queryExplainer = display.querySelector('#queryexplainer')

    const explain_tag = {
        EmptyQuery(x) {
            return "<empty>"
        },
        NameQuery(x) {
            return `name(${x.contents})`
        },
        ReturnQuery(x) {
            return `return-type(${x.contents})`
        },
        ParamQuery(x) {
            return `takes(${x.contents.join(", ")})`
        },
        ExtendsQuery(x) {
            return `extends(${x.contents})`
        },
        SumQuery(x) {
            return `combined-score(${x.contents.map(explain_query).join(", ")})`
        },
        MinQuery(x) {
            return `best-of(${x.contents.map(explain_query).join(", ")})`
        }
    }

    function explain_query(ast) {
        const tag = ast.tag
        return explain_tag[tag](ast)
    }

    function after_timeout(){
        var value = bar.value
        if(! value)
            return
        
        window.history.replaceState(null, "", $SCRIPT_ROOT+"search?query="+value)

        var on_load = function(){
            var json = JSON.parse(this.responseText)

            queryExplainer.innerHTML = ""
            // explain_query(json.queryParsed, queryExplainer)
            queryExplainer.textContent = explain_query(json.queryParsed)



            results.innerHTML = ""
            json.results.forEach(function(v){
                var div = document.createElement("div")
                var code = tokenize(v, "code", jass_tokens)
                div.setAttribute("class", "result")
                div.appendChild(code)
                results.appendChild(div)
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
