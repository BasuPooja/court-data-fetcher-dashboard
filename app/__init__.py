import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import config
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app, db)

    from .models import CaseQuery, ParsedCaseDetails # ⬅️ Import your models before create_all
    from .routes import main       # ⬅️ Import and register blueprint

    with app.app_context():
        db.create_all()  # ⬅️ Now creates tables for CaseQuery and other models

    # Register blueprint
    app.register_blueprint(main)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html'), 500

    return app
