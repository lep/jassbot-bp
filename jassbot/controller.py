import datetime
import json
import socket
import sqlite3
from functools import lru_cache
from urllib.parse import urlencode

import flask
import markdown
import requests
from flask import (
    Blueprint,
    current_app,
    g,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from jassbot.model import Model
from jassbot.trie import Trie


def getmodel():
    if "jassbot_db" not in g:
        g.jassbot_db = Model(sqlite3.connect(current_app.config["JASSBOT"]["DB"]))
    return g.jassbot_db

def get_markdown_renderer():
    if "jassbot_markdown_render" not in g:
        g.jassbot_markdown_render = markdown.Markdown(extensions=['tables', 'fenced_code', 'attr_list'])
    return g.jassbot_markdown_render


@lru_cache
def md(txt):
    if not txt:
        return ""
    return get_markdown_renderer().reset().convert(txt)

def mk_syntax_regexps(db):
    def mk(ls):
        plain = "/^(?:" + "|".join(ls) + ")\\b/"
        t = Trie()
        for l in ls:
            t.insert(l)
        fancy = "/^" + t.toRegexp() + "\\b/"
        if len(fancy) < len(plain):
            return fancy
        else:
            return plain

    return "\n".join([
        "const bj_globals = " + mk(db.query_bj_globals()),
        "const cj_globals = " + mk(db.query_cj_globals()),
        "const natives = " + mk(db.query_natives()),
        "const functions = " + mk(db.query_functions()),
        "const types = " + mk(db.query_types()),
    ])

@lru_cache(maxsize=2)
def cached_syntax_regexps(_commit):
    return mk_syntax_regexps(getmodel())

def query_jassbot(query):
    r = requests.get(f"{current_app.config['JASSBOT']['API']}?q={query}", stream=True)
    def generator():
        for x in r.iter_lines():
            yield x
    return generator()

def mk_bp(*args, **kwargs):
    bp = Blueprint("jassbot", __name__, template_folder="templates", static_folder="static", **kwargs)

    @bp.route("/")
    def index():
        return render_template("jassbot/index.html.j2")

    @bp.route("/doc/")
    def empty_doc():
        return redirect(url_for('.index'))

    @bp.route('/search/api/<query>')
    def search_api(query):
        return query_jassbot(query), {"Content-Type": "application/json"}


    @bp.route("/search")
    def search():
        if query := request.args.get('query', ''):
            res = json.loads( b"".join( list(query_jassbot(query))) )
            return render_template('jassbot/search.html.j2',
                                   results=res['results'],
                                   queryParsed=res['queryParsed'],
                                   query=query)
        else:
            return redirect(url_for('.index'))

    @bp.route("/opensearch.xml")
    def opensearch():
        domain = request.url_root
        return render_template('jassbot/opensearch.xml.j2', domain=domain), 200, {
            'Content-Type': 'text/xml'
        }

    @bp.route("/syntax.js")
    def syntax_regexps():
        db = getmodel()
        commit = db.query_git_commit()

        # We have to use a "weak" etag here, because the spec says if the
        # response is changed - like for example by gzipping it - it has to be
        # changed. Since we let nginx gzip our responses we have to use a weak
        # etag, otherwise it would always be served fresh.
        return cached_syntax_regexps(commit), 200, {
            'Content-Type': 'text/javascript',
            'ETag': f'W/"{commit}"',
        }

    @bp.route("/doc/<entity>")
    def doc(entity):
        db = getmodel()

        commit = db.query_git_commit()

        parameters = []
        for param in db.query_function_parameters(entity):
            param['html'] = md(param['doc'])
            parameters.append(param)
        linenumber = db.query_line_number(entity)
        kind = db.query_type(entity)

        annotations = []
        for annotation in db.query_annotations(entity):
            if annotation['name'] == 'async':
                annotations.append({"name": "async", "html": "This function is asynchronous. The values it returns are not guaranteed to be the same for each player. If you attempt to use it in an synchronous manner it may cause a desync."})
            elif annotation['name'] == 'pure':
                annotations.append({"name": "pure", "html": "This function is pure. For the same values passed to it, it will always return the same value."})
            elif annotation['name'] == 'source-file':
                fileName = annotation['value']
                permalink = 'https://github.com/lep/jassdoc/blob/%s/%s#L%s' % (commit, fileName, linenumber)
                sourceFileLinkHtml = '<a href="%s" rel="nofollow" >%s</a>' % (permalink, fileName)
                # New issue link accepts either body or permalink, not both. Maybe aliases of one another.
                newIssueLinkEncoded = 'https://github.com/lep/jassdoc/issues/new?' + urlencode(
                    { "title": "[web] %s: %s - " % (fileName, entity),
                      "body": permalink + "\n\nPlease change to a good descriptive title and tell us what should be improved.",
                    })
                editLink = 'https://github.com/lep/jassdoc/edit/master/%s#L%s' % (fileName, linenumber)
                discussHtml = '(<a href="%s" rel="nofollow" >suggest an edit</a> or <a href="%s">discuss on Github</a>)' % (editLink, newIssueLinkEncoded)
                annotations.append({"name": "Source", "html": sourceFileLinkHtml + " " + discussHtml})
            elif annotation['name'] == 'source-code':
                annotations.append({"name": "Source code", "html": "<pre><code>%s</code></pre>" % annotation['value']})
            elif annotation['name'] == 'return-type':
                annotations.append({"name": "return type", "html": "<code>%s</code>" % annotation['value']})
            elif annotation['name'] == 'commonai':
                annotations.append({"name": "common.ai native", "html": "To use this native you have to declare it in your script."})
            elif annotation['name'] == 'event':
                annotations.append({"name": "event", "html": f"<code>{annotation['value']}</code>"})
            else:
                annotations.append({"name": annotation['name'], "html": md(annotation['value'])})


        response = render_template('jassbot/doc.html.j2', kind=kind, entity=entity, parameters=parameters, annotations=annotations)
        etag = f'W/"{commit}"'
        return response, 200, { 'ETag': etag }

    @bp.route("/doc/api/<entity>")
    def doc_api(entity):
        db = getmodel()

        commit = db.query_git_commit()

        parameters = list( db.query_function_parameters(entity) )
        linenumber = db.query_line_number(entity)
        kind = db.query_type(entity)
        annotations = list( db.query_annotations(entity) )
        return {'commit': commit,
                'parameters': parameters,
                'annotations': annotations,
                'linenumber': linenumber,
                'kind': kind
                }

    @bp.errorhandler(404)
    @bp.errorhandler(Exception)
    def page_not_found(error):
        return render_template('jassbot/404.html.j2'), 404

    @bp.context_processor
    def is_birthday():
        today = datetime.date.today()
        if today.month == 2 and today.day == 8:
            birthday = datetime.date(2016, 2, 8)
            how_old = today - birthday
            years = how_old.days // 365
            units = years % 10
            tens = years % 100
            if units == 1 and tens != 11:
                suffix = "st"
            elif units == 2 and tens != 12:
                suffix = "nd"
            elif units == 3 and tens != 13:
                suffix = "rd"
            else:
                suffix = "th"

            return { "birthday": f"{years}{suffix}"}
        else:
            return {}

    return bp

