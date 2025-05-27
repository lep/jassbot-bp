#!/usr/bin/env python3

from flask import Flask
import jassbot

app = Flask(__name__)
app.config.from_prefixed_env()
app.config["SERVER_NAME"] = "localhost:5000"
app.register_blueprint(jassbot.mk_bp(url_prefix="/jassbot"))

if __name__ == '__main__':
    app.run("localhost", 5000, debug=True)
