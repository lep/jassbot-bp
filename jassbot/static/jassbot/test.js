const jass_keywords = /^(:?debug|set|call|and|or|not|takes|returns|type|extends|native|constant|globals|endglobals|local|return|if|then|else|elseif|endif|loop|exitwhen|endloop|function|endfunction)\b/
const jass_tokens = [
  [jass_keywords, "keyword"]
, [functions, "bj"]
, [types, "type"]
, [natives, "native"]
, [bj_globals, "bjglobal"]
, [cj_globals, "cjglobal"]
, [/^(?:\/\/.+(\n|$))/, "comment"]
, [/^(?:0x[a-f0-9]+)/i, "number"]
, [/^(?:\$[a-f0-9]+)/i, "number"]
, [/^(?:\d+\.\d+)/, "number"]
, [/^(?:\d+\.)/, "number"]
, [/^(?:\.\d+)/, "number"]
, [/^(?:\d+)/, "number"]
, [/^(?:true|false)\b/, "bool"]
, [/^(?:null)\b/, "null"]
, [/^(?:array|nothing)\b/, "like-type"]
, [/^(?:\"(?:[^\"\\]|\\[\s\S])*(?:\"|$))/, "string"]
, [/^(?:\'(?:[^\'\\]|\\[\s\S])*(?:\'|$))/, "rawcode"]
, [/^(?:[-<>+*/%=!,()\[\]]+)/, "operator"]
, [/^(?:\w+)/, "ident"]
, [/^(?:[ \t]+)/, "ws"]
, [/^./, "anything"]
, [/^\n/, "anything"]
, [/^$/, "anything"]
]

const lua_keywords = /^(:?and|break|do|else|elseif|end|false|for|function|if|in|local|nil|not|or|repeat|return|then|true|until|while)\b/
const lua_tokens = [
  [lua_keywords, "keyword"]
, [functions, "bj"]
, [types, "type"]
, [natives, "native"]
, [bj_globals, "bjglobal"]
, [cj_globals, "cjglobal"]
, [/^(?:--\[(=*)\[.*?]\1])/s, "comment"]
, [/^(?:--.+(\n|$))/, "comment"]
, [/^(?:\[\[.*?]])/, "string"]
, [/^(?:0x[a-f0-9]+)/i, "number"]
, [/^(?:\d+\.\d+)/, "number"]
, [/^(?:\d+\.)/, "number"]
, [/^(?:\.\d+)/, "number"]
, [/^(?:\d+)/, "number"]
, [/^(?:\[(=*)\[.*?]\1])/s, "string"]
, [/^(?:\"(?:[^\"\\]|\\[\s\S])*(?:\"|$))/, "string"]
, [/^(?:\'(?:[^\'\\]|\\[\s\S])*(?:\'|$))/, "string"]
, [/^(?:[-<>#;:~+.*/%=^,()\[\]])/, "operator"]
, [/^(?:\w+)/, "ident"]
, [/^(?:[ \t]+)/, "ws"]
, [/^./, "anything"]
, [/^\n/, "anything"]
, [/^$/, "anything"]
]

function mkdom(txt, type){
    var span = document.createElement("span")
    var linkit = new Set(["native", "bj", "bjglobal", "cjglobal", "type"])
    if( linkit.has(type) ){
        span.innerHTML = "<a href='"+$SCRIPT_ROOT+"doc/"+txt+"'>"+txt+"</a>"
    }else {
        span.innerText = txt
    }
    span.setAttribute("class", type)
    return span

}

function tokenize(txt, type, tokens){
    let res = []
    let span = document.createElement(type)
    span.setAttribute("class", "highlighted")
    while(txt){
        for(let i = 0; i != tokens.length; i++){
            const match = txt.match(tokens[i][0])
            if(match){
                const dom = mkdom(match[0], tokens[i][1])
                span.appendChild(dom)
                txt = txt.slice(match[0].length)
                break
            }
        }
    }
    return span
}

function hl(){
    document.querySelectorAll("code").forEach(pre => {
        if( ! pre.classList.contains("sourceCode")){ // pandoc hl
            if( pre.classList.contains("language-lua") || pre.classList.contains("lua") ){
                pre.replaceWith(tokenize(pre.textContent, "code", lua_tokens))
            }else{
                pre.replaceWith(tokenize(pre.textContent, "code", jass_tokens))
            }
        }
    })
}
