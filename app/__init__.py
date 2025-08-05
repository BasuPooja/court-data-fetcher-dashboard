import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config.from_pyfile(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py'))

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///court_queries.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .models import CaseQuery
    from .routes import main

    app.register_blueprint(main)

    # ✅ Add error handlers here
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html'), 500

    return app
