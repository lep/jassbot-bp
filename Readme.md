This is the flask [blueprint](https://flask.palletsprojects.com/en/2.2.x/blueprints/)
which serves the jassbot [web interface](https://lep.duckdns.org/jassbot).

# Installation

## Prerequisites

You need to have a valid [jass.db](https://github.com/lep/jassdoc) somewhere
around to really use this. Once you've achieved this you need to tell the
Blueprint where to find the database. To do that you have to define an
environment variable called `FLASK_JASSBOT__DB` pointing at your jass.db like this:

    $ export FLASK_JASSBOT__DB=/path/to/your/jass.db

## Installation via pip

I have only done the minimal work to get pip/setuptools work with my nix flake
but it seems to work. 

    # probably want to do this in a venv
    $ python3 -m pip install git+https://github.com/lep/jassbot-bp

Once that is done you can either register `jassbot.mk_bp()` in your own flask
app or (which is more likely) you can run a *dev* setup like this

    # i hope you have set your FLASK_JASSBOT__DB env var
    $ flask run

Now you should be able to visit <http://localhost:5000/jassbot>.

## Extra functionality

Do note though that if you've got this running the search functionality wont
work out of the box as that is provided by another service. Navigating to a
specific doc page *should* still work but if you want to have the search running
aswell you have to install the [jassbot](https://github.com/lep/jassbot) utility
and run the web component like `cabal run ng`. The address of the jassbot server
should be configured via the `FLASK_JASSBOT__API` environment variable.
