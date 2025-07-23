#!/usr/bin/env python3

import flask
from flask import Blueprint
from flask import current_app, g, request, make_response
from flask import render_template, redirect, url_for

import sqlite3
import markdown
from functools import lru_cache
import socket
import json
import requests
from urllib.parse import urlencode

from jassbot.trie import Trie

class Model:
    def __init__(self, db):
        self.db = db

    def query_function_parameters(self, fnname):
        cur = self.db.cursor()
        cur.execute("""
            select Ty.param, Ty.value, Doc.value from
            ( select Value, param
              from Params_extra
              where Anname == 'param_order' AND fnname == :fnname
            ) as Ord

            inner join
            ( select param, value
              from params_extra
              where anname == 'param_type' and fnname == :fnname
            ) as Ty on Ty.param == Ord.param

            left outer join
            ( select param, value from parameters
              where fnname == :fnname
            ) as Doc on Doc.param == Ord.param

            order by Ord.value
        """, { "fnname": fnname })
        for name, ty, doc in cur:
            yield { "name": name, "type": ty, "doc": doc }
        cur.close()

    def query_annotations(self, entity):
        cur = self.db.cursor()
        cur.execute("""
            select anname, value
            from annotations
            where fnname == ? and anname not in ('type', 'start-line', 'end-line')
            -- we rely on sqlite here to get the annotations in order as they
            -- are in the docstring, because we insert them in that order.
            order by rowid
        """, (entity, ))
        for name, value in cur:
            yield { "name": name, "value": value }
        cur.close()

    def query_line_number(self, entity):
        cur = self.db.cursor()
        cur.execute("""
            select value
            from annotations
            where fnname == ? and anname == 'start-line'
        """, (entity,))
        row = cur.fetchone()
        cur.close()
        return row[0]

    def query_type(self, entity):
        cur = self.db.cursor()
        cur.execute("""
            select value
            from annotations
            where fnname == ? and anname == 'type'
        """, [entity])
        row = cur.fetchone()
        cur.close()
        return row[0]

    def query_git_commit(self):
        cur = self.db.cursor()
        cur.execute("""
            select value
            from metadata
            where key = 'git-commit'
        """)
        row = cur.fetchone()
        cur.close()
        return row[0]

    def query_bj_globals(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='global'
                AND fnname LIKE 'bj_%'
        """)
        return list(x[0] for x in cur.fetchall())

    def query_cj_globals(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='global'
                AND fnname NOT LIKE 'bj_%'
        """)
        return list(x[0] for x in cur.fetchall())

    def query_natives(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='native'
        """)
        return list(x[0] for x in cur.fetchall())

    def query_functions(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='function'
        """)
        return list(x[0] for x in cur.fetchall())

    def query_types(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT fnname
            FROM annotations
            WHERE anname == 'type'
                AND value =='type'
        """)
        return list(x[0] for x in cur.fetchall())


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

    regexp_cache_key = None
    regexp_cache_value = None
    @bp.route("/syntax.js")
    def syntax_regexps():
        db = getmodel()
        commit = db.query_git_commit()
        # We have to use a "weak" etag here, because the spec says if the
        # response is changed - like for example by gzipping it - it has to be
        # changed. Since we let nginx gzip our responses we have to use a weak
        # etag, otherwise it would always be served fresh.
        etag = f'W/"{commit}"'
        nonlocal regexp_cache_value
        nonlocal regexp_cache_key

        if regexp_cache_value is None or regexp_cache_key != commit:
            regexp_cache_key = commit
            regexp_cache_value = mk_syntax_regexps(db)

        if request.headers.get("If-None-Match") == etag:
            return "", 304

        return regexp_cache_value, 200, {
            'Content-Type': 'text/javascript',
            'ETag': etag,
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
        

        return render_template('jassbot/doc.html.j2', kind=kind, entity=entity, parameters=parameters, annotations=annotations)

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


    return bp

def create_app(*args, **kwargs):
    app = flask.Flask(__name__)
    app.config.from_prefixed_env()
    app.register_blueprint(mk_bp(*args, **kwargs))
    return app
