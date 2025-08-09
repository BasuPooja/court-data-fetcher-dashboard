import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from jinja2 import StrictUndefined
import config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models before creating tables
    from .models import CaseQuery, ParsedCaseDetails
    from .routes import main  # Import blueprint

    with app.app_context():
        db.create_all()  # Create tables if not exist

    # Register blueprint
    app.register_blueprint(main)

    # Make Jinja throw errors for undefined vars
    app.jinja_env.undefined = StrictUndefined

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Rollback in case of DB errors
        return render_template('error.html'), 500

    return app
