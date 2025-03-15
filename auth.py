from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash

from models import db, User

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Expects JSON: { "username": "...", "password": "..." }
    On success, returns { "access_token": "..." }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data"}), 400

    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Create a JWT, embedding user info
    access_token = create_access_token(
        identity={"username": user.username, "role": user.role}
    )
    return jsonify({"access_token": access_token}), 200

def role_required(allowed_roles):
    """
    Decorator that requires JWT auth, then checks if the user's role 
    is in allowed_roles. If not, returns 403.
    """
    from functools import wraps

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()  # e.g. {"username": "admin", "role": "Admin"}
            if current_user["role"] not in allowed_roles:
                return jsonify({"error": "Insufficient privileges"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
