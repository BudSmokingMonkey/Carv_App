import logging
from flask import Flask, render_template
from flask_jwt_extended import JWTManager

# Your config class with environment-based secrets
from config import Config

# Your SQLAlchemy models, plus a helper to create an admin user if needed
from models import db, seed_admin_user

# Existing auth / login blueprint
from auth import auth_bp

# Existing routes
from routes.cars import cars_bp
from routes.reservations import reservations_bp

# Existing blueprint for API connections
from routes.api_connections import apis_bp

# NEW: the blueprint for email reservations
# Make sure routes/email_reservations.py exists and defines `email_res_bp`
from routes.email_reservations import email_res_bp


def create_app():
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    # Init database and JWT
    db.init_app(app)
    jwt = JWTManager(app)

    # Basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    # Create tables and seed an admin user if not present
    with app.app_context():
        db.create_all()
        seed_admin_user(db)

    # Register your blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(cars_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(apis_bp)
    # The new one for email reservations:
    app.register_blueprint(email_res_bp)

    # Serve your main dashboard
    @app.route("/")
    def dashboard():
        return render_template("dashboard.html")
    
    return app


# If you run `python app.py`, this starts the dev server.
if __name__ == "__main__":
    my_app = create_app()
    my_app.run(debug=True)
