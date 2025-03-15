from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Car, ALLOWED_GROUPS, ALLOWED_STATUSES
from auth import role_required

cars_bp = Blueprint("cars_bp", __name__)

def validate_car_data(data, partial=False):
    """ Validate incoming JSON data for Car creation or update. """
    if not partial:
        # Must have model, car_group, status
        for field in ["model", "car_group", "status"]:
            if field not in data:
                return False, f"Missing '{field}' in JSON."

    # car_group check
    if "car_group" in data:
        if data["car_group"] not in ALLOWED_GROUPS:
            return False, f"Invalid car_group '{data['car_group']}'. Must be one of {ALLOWED_GROUPS}."

    # status check
    if "status" in data:
        if data["status"] not in ALLOWED_STATUSES:
            return False, f"Invalid status '{data['status']}'. Must be one of {ALLOWED_STATUSES}."

    return True, None

@cars_bp.route("/api/v1/cars", methods=["GET"])
@jwt_required()
def list_cars():
    """
    GET all cars with optional filtering/pagination/sorting
    Query params:
      - page, per_page
      - status, car_group
      - search (partial match on model)
      - sort_by, direction
    """
    query = Car.query

    # Filtering
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    car_group = request.args.get("car_group")
    if car_group:
        query = query.filter_by(car_group=car_group)

    # Search by model
    search = request.args.get("search")
    if search:
        query = query.filter(Car.model.ilike(f"%{search}%"))

    # Sorting
    sort_by = request.args.get("sort_by", "id")
    direction = request.args.get("direction", "asc")
    valid_cols = {"id", "model", "car_group", "status", "year", "daily_rate", "location"}
    if sort_by not in valid_cols:
        sort_by = "id"

    order_col = getattr(Car, sort_by)
    if direction == "desc":
        order_col = order_col.desc()

    query = query.order_by(order_col)

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    cars = [c.to_dict() for c in pagination.items]

    response = {
        "cars": cars,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages
    }
    return jsonify(response), 200

@cars_bp.route("/api/v1/cars/<int:car_id>", methods=["GET"])
@jwt_required()
def get_car(car_id):
    car = Car.query.get_or_404(car_id)
    return jsonify(car.to_dict()), 200

@cars_bp.route("/api/v1/cars", methods=["POST"])
@role_required(["Admin", "Rental Team"])  # e.g. only admins/rental team can add cars
def add_car():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    is_valid, error_msg = validate_car_data(data, partial=False)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    new_car = Car(
        model=data["model"],
        car_group=data["car_group"],
        status=data["status"],
        year=data.get("year"),
        daily_rate=data.get("daily_rate"),
        location=data.get("location")
    )
    db.session.add(new_car)
    db.session.commit()
    return jsonify({"message": "Car added successfully!", "car_id": new_car.id}), 201

@cars_bp.route("/api/v1/cars/<int:car_id>", methods=["PUT", "PATCH"])
@role_required(["Admin", "Rental Team"])
def update_car(car_id):
    car = Car.query.get_or_404(car_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data"}), 400

    partial = (request.method == "PATCH")
    is_valid, error_msg = validate_car_data(data, partial=partial)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    if "model" in data:
        car.model = data["model"]
    if "car_group" in data:
        car.car_group = data["car_group"]
    if "status" in data:
        car.status = data["status"]
    if "year" in data:
        car.year = data["year"]
    if "daily_rate" in data:
        car.daily_rate = data["daily_rate"]
    if "location" in data:
        car.location = data["location"]

    db.session.commit()
    return jsonify({"message": "Car updated"}), 200

@cars_bp.route("/api/v1/cars/<int:car_id>", methods=["DELETE"])
@role_required(["Admin"])
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)
    db.session.delete(car)
    db.session.commit()
    return jsonify({"message": "Car deleted"}), 200

@cars_bp.route("/api/v1/cars/bulk", methods=["POST"])
@role_required(["Admin", "Rental Team"])
def bulk_add_cars():
    """
    Accepts a JSON array of car objects.
    e.g.
    [
      { "model": "Toyota Corolla", "car_group": "ICAR", "status": "available" },
      { "model": "Honda Civic",   "car_group": "CDAR", "status": "maintenance" }
    ]
    """
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Expected a JSON array of car objects"}), 400

    new_car_ids = []
    for car_data in data:
        is_valid, error_msg = validate_car_data(car_data, partial=False)
        if not is_valid:
            return jsonify({"error": error_msg, "data": car_data}), 400

        new_car = Car(
            model=car_data["model"],
            car_group=car_data["car_group"],
            status=car_data["status"],
            year=car_data.get("year"),
            daily_rate=car_data.get("daily_rate"),
            location=car_data.get("location")
        )
        db.session.add(new_car)
        db.session.flush()  # get the ID before commit
        new_car_ids.append(new_car.id)

    db.session.commit()
    return jsonify({"message": f"Added {len(new_car_ids)} cars", "car_ids": new_car_ids}), 201
