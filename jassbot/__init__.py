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


def getmodel():
    if "jass_db" not in g:
        g.jass_db = Model(sqlite3.connect(current_app.config["JASSDB"]))
    return g.jass_db

def get_markdown_renderer():
    if "md" not in g:
        g.md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    return g.md


@lru_cache
def md(txt):
    if not txt:
        return ""
    return get_markdown_renderer().reset().convert(txt)

bp = Blueprint("jassbot", __name__, url_prefix="/jassbot", template_folder="templates", static_folder="static")

def query_jassbot(query):
    r = requests.get(f"{current_app.config['JASSBOT_API']}?q={query}", stream=True)
    def generator():
        for x in r.iter_lines():
            yield x
    return generator()

@bp.route("/")
def index():
    return render_template("jassbot/index.html.j2")

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
            annotations.append({"name": "Source", "html": '<a href="https://github.com/lep/jassdoc/blob/%s/%s#L%s">%s</a>' % (commit, annotation['value'], linenumber, annotation['value']) })
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
    return render_template('jassbot/404.html'), 404

def create_app():
    app = flask.Flask(__name__)
    app.config.from_prefixed_env()
    app.register_blueprint(bp)
    return app
