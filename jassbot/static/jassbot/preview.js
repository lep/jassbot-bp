function setup(){
    const searchbar = document.getElementById("search")
    const display = document.getElementById("result")
    const results = display.querySelector('.results')
    const queryExplainer = document.getElementById('queryexplainer')

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

    const explain_query = (ast) => explain_tag[ast.tag](ast)

    let pushstate_timer = null
    let typing_timer = null

    const populate_search_results = (ev) => {
        let value = ""
        let json = { results: [] }
        if( ev ){
            json = ev.json
            value = ev.value
        }
        searchbar.value = value
        results.innerHTML = ""
        json.results.forEach(function(v){
            const div = document.createElement("div")
            const code = tokenize(v, "code", jass_tokens)
            div.setAttribute("class", "result")
            div.appendChild(code)
            results.appendChild(div)
        })
    }

    const after_timeout = async () => {
        const value = searchbar.value
        if(! value) return

        const url = new URL($SCRIPT_ROOT+"search", window.location.origin)
        url.searchParams.set("query", value)

        if( pushstate_timer ) clearTimeout(pushstate_timer)

        const response = await fetch(new URL("search/api/"+value, url))
        const json = await response.json()
        queryExplainer.innerHTML = ""
        queryExplainer.textContent = explain_query(json.queryParsed)

        const state = { json, value }
        pushstate_timer = setTimeout(() => window.history.pushState(state, "", url), 200)
        populate_search_results(state)
    }

    searchbar.addEventListener('keyup', () => {
        if( typing_timer ) clearTimeout(typing_timer)
        if( pushstate_timer ) clearTimeout(pushstate_timer)
        typing_timer = setTimeout(after_timeout, 150)
    })

    addEventListener("popstate", (event) => populate_search_results(event.state))
}
