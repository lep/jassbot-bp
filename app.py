from flask import Flask
import jassbot

app = Flask(__name__)
app.config.from_prefixed_env()
app.register_blueprint(jassbot.bp)

if __name__ == '__main__':
    app.run("localhost", 5000, debug=True)

