import os
from flask import Flask

def create_app():
    app = Flask(__name__)

    # Load config from the root config.py using absolute path
    app.config.from_pyfile(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py'))

    from .routes import main
    app.register_blueprint(main)

    return app
