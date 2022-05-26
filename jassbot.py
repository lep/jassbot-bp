#!/usr/bin/env python3

import flask
from flask import Blueprint
from flask import current_app, g, request
from flask import render_template, redirect, url_for

import sqlite3
import markdown
from functools import lru_cache
import socket
import json

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
            order by anname
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
        g.md = markdown.Markdown(extensions=['tables'])
    return g.md


@lru_cache
def md(txt):
    if not txt:
        return ""
    return get_markdown_renderer().reset().convert(txt)

bp = Blueprint("jassbot", __name__, url_prefix="/jassbot")

def query_jassbot(query):
        s = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
        s.connect("/tmp/jassbot-api.sock")
        s.send( query.encode() )
        chunks = []
        while (chunk := s.recv(4096)) != b'':
            chunks.append(chunk)
        answer = b''.join(chunks).decode()
        return json.loads(b''.join(chunks).decode())


@bp.route("/")
def index():
    return render_template("jassbot/index.html.j2")

@bp.route('/search/api/<query>')
def search_api(query):
    return flask.json.dumps(query_jassbot(query))


@bp.route("/search")
def search():
    if query := request.args.get('query', ''):
        results = query_jassbot(query)
        return render_template('jassbot/search.html.j2', results=results, query=query)
    else:
        return redirect(url_for('.index'))



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
            annotations.append({"name": "Source code", "html": "<pre>%s</pre>" % annotation['value']})
        elif annotation['name'] == 'return-type':
            annotations.append({"name": "return type", "html": "<code>%s</code>" % annotation['value']})
        else:
            annotations.append({"name": annotation['name'], "html": md(annotation['value'])})
        

    return render_template('jassbot/doc.html.j2', kind=kind, entity=entity, parameters=parameters, annotations=annotations)

