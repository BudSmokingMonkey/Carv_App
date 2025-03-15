# routes/email_reservations.py

import os
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file

from fetch_email import fetch_unread_emails
from format_data import format_all_reservations
from generate_pdf import PDFGenerator

email_res_bp = Blueprint("email_res_bp", __name__)

@email_res_bp.route("/api/v1/email_reservations/fetch", methods=["POST"])
def fetch_email_reservations():
    """
    1) Fetch unread reservation emails via IMAP
    2) Format them
    3) Return as JSON
    """
    new_reservations = fetch_unread_emails()  # raw from email
    formatted = format_all_reservations(new_reservations)
    return jsonify({"reservations": formatted})


@email_res_bp.route("/api/v1/email_reservations/pdf", methods=["POST"])
def email_reservations_pdf():
    """
    Expects JSON of the form:
      {
        "reservations": [
          {
            "Booking Code": "...",
            "Customer Name": "...",
            ...
          },
          ...
        ]
      }

    Generates a PDF of those reservations, then returns it as a file.
    """
    data = request.json
    if not data or "reservations" not in data:
        return jsonify({"error": "No reservations provided."}), 400

    reservations_list = data["reservations"]

    # Generate a temporary PDF file using PDFGenerator
    temp_pdf_path = "temp_email_reservations.pdf"
    pdf_gen = PDFGenerator(filename=temp_pdf_path)
    pdf_gen.create_report(reservations_list)

    # Read the PDF into memory
    with open(temp_pdf_path, "rb") as f:
        pdf_data = f.read()

    # Clean up the temp file
    if os.path.exists(temp_pdf_path):
        os.remove(temp_pdf_path)

    # Return the PDF as an attachment
    return send_file(
        BytesIO(pdf_data),
        as_attachment=True,
        download_name="new_email_reservations.pdf",
        mimetype="application/pdf"
    )
