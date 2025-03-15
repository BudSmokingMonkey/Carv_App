# routes/email_extractor.py

import os
from io import BytesIO

from flask import Blueprint, request, jsonify, send_file
from fetch_email import fetch_unread_emails
from format_data import format_all_reservations
from generate_pdf import PDFGenerator

email_extractor_bp = Blueprint('email_extractor_bp', __name__)

@email_extractor_bp.route("/api/v1/extract_and_pdf", methods=["POST"])
def extract_and_generate_pdf():
    """
    1) Fetch unread emails from IMAP
    2) Parse & format them
    3) Generate PDF of all newly found reservations
    4) Return the PDF to the browser
    """
    try:
        # --- 1) Fetch unread emails ---
        raw_reservations = fetch_unread_emails()

        # --- 2) Format them ---
        formatted_list = format_all_reservations(raw_reservations)

        # If no new reservations, you might want to handle that gracefully:
        if not formatted_list:
            return jsonify({"error": "No new reservations found."}), 404

        # --- 3) Generate PDF ---
        pdf_filename = "temp_new_reservations.pdf"
        pdf_gen = PDFGenerator(pdf_filename)
        pdf_gen.create_report(formatted_list)

        # --- 4) Return PDF as a file attachment ---
        with open(pdf_filename, "rb") as f:
            pdf_data = f.read()
        os.remove(pdf_filename)  # Clean up the temp file

        return send_file(
            BytesIO(pdf_data),
            as_attachment=True,
            download_name="new_email_reservations.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        # On any error, return JSON
        return jsonify({"error": str(e)}), 500
