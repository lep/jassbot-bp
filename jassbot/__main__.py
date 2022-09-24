from flask import Flask
import jassbot

app = Flask(__name__)
app.register_blueprint(jassbot.bp)
app.config.from_prefixed_env()


if __name__ == "__main__":
    app.run(debug=True)
