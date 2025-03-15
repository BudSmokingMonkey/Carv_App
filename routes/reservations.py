from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
from datetime import datetime, date
from flask_jwt_extended import jwt_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER

from models import db, Reservation, Car
from auth import role_required

reservations_bp = Blueprint("reservations_bp", __name__)

@reservations_bp.route("/api/v1/reservations", methods=["GET"])
@jwt_required()
def list_reservations():
    """
    GET /api/v1/reservations
    Optional params:
      - date_filter (str) => "today", "this_week", etc. (just a demo)
    """
    query = Reservation.query

    date_filter = request.args.get("date_filter")
    if date_filter == "today":
        today_date = date.today()
        query = query.filter(
            (Reservation.start_date == today_date) | 
            (Reservation.end_date == today_date)
        )

    reservations = [r.to_dict() for r in query.all()]
    return jsonify(reservations), 200

@reservations_bp.route("/api/v1/reservations", methods=["POST"])
@role_required(["Admin", "Rental Team", "Service Team"])
def create_reservation():
    """
    Expects JSON:
    {
      "customer_name": "...",
      "car_id": 123,
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data"}), 400

    customer_name = data.get("customer_name")
    car_id = data.get("car_id")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if not customer_name or not car_id or not start_date_str or not end_date_str:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    car = Car.query.get(car_id)
    if not car:
        return jsonify({"error": "Car not found"}), 404

    new_res = Reservation(
        customer_name=customer_name,
        car_id=car_id,
        start_date=start_d,
        end_date=end_d,
        status="booked"
    )
    db.session.add(new_res)
    db.session.commit()
    return jsonify({"message": "Reservation created", "reservation_id": new_res.id}), 201

@reservations_bp.route("/api/v1/reservations/<int:res_id>/pdf", methods=["GET"])
@jwt_required()
def reservation_prefill_pdf(res_id):
    """
    Example of generating a PDF with ReportLab and returning it.
    """
    res = Reservation.query.get_or_404(res_id)

    # 1) Create a BytesIO buffer
    pdf_buffer = BytesIO()

    # 2) Build PDF using ReportLab
    c = canvas.Canvas(pdf_buffer, pagesize=LETTER)
    c.drawString(100, 700, f"Reservation #{res.id}")
    c.drawString(100, 680, f"Customer: {res.customer_name}")
    c.drawString(100, 660, f"Car ID: {res.car_id}")
    c.drawString(100, 640, f"Start Date: {res.start_date}")
    c.drawString(100, 620, f"End Date: {res.end_date}")
    c.drawString(100, 600, f"Status: {res.status}")
    c.showPage()
    c.save()

    pdf_buffer.seek(0)

    # 3) Return file to user
    filename = f"reservation_{res.id}.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")
