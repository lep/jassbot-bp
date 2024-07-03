This is the flask [blueprint](https://flask.palletsprojects.com/en/2.2.x/blueprints/)
which serves the jassbot [web interface](https://lep.duckdns.org/jassbot).

# Installation

## Prerequisites

You need to have a valid [jass.db](https://github.com/lep/jassdoc) somewhere
around to really use this. Once you've achieved this you need to tell the
Blueprint where to find the database. To do that you have to define an
environment variable called `FLASK_JASSDB` pointing at your jass.db like this:

    $ export FLASK_JASSDB=/path/to/your/jass.db


## Installation via pip

I have only done the minimal work to get pip/setuptools work with my nix flake
but it seems to work. To install this package you can use pip like this

    $ python3 -m pip install git+https://github.com/lep/jassbot-bp

Once that is done you can either register `jassbot.bp` in your own flask app or
(which is more likely) you can run a *dev* setup like this

    $ python3 -m jassbot # i hope you have set your FLASK_JASSDB env var

Now you should be able to visit <http://localhost:5000/jassbot>.


## Installation via nix

If you have a working [nix/nixos](https://nixos.org/) installation you
can directly run it via `nix run github:lep/jassbot-bp`. As a nix goodyness you
actually get the [jass.db](https://github.com/lep/jassdoc) for "free" (well you
still have to compile it, but that should be done automatically). Again, running
it like this should only be done for your *dev* environment.
I also provide a dev shell in the flake with the `jassbot` module ready.

## Extra functionality

Do note though that if you've got this running the search functionality wont
work out of the box as that is provided by another service. Navigating to a
specific doc page *should* still work but if you want to have the search running
aswell you have to install the [jassbot](https://github.com/lep/jassbot) utility
and run the web component like `cabal run web` or
`nix run github:lep/jassbot#web`.
