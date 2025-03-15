import time
from fpdf import FPDF


class PDFGenerator:
    """
    A simple PDF generator that takes a list of reservations (dicts) and
    creates one page per reservation.

    Each reservation is expected to have:
        "Start Date & Time",
        "End Date & Time",
        "Flight Number",
        "Customer Name",
        "Booking Code",
        "Car Class",
        "Insurance"
    """

    def __init__(self, filename=None):
        """
        If filename is None, we create a timestamp-based filename,
        like "carvenience_report_20250314_153012.pdf".
        """
        if filename:
            self.filename = filename
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.filename = f"carvenience_report_{timestamp}.pdf"

        self.pdf = FPDF(orientation="P", unit="mm", format="A4")
        self.page_width = 210
        self.page_height = 297

        # Decide on base font sizes
        self.base_font_size = 24  # For most text
        self.name_font_size = self.base_font_size + 12  # 4 points bigger

        # Decide on line spacing
        self.line_height = 9  # for normal lines
        self.big_line_height = 12  # for the bigger name lines

    def create_report(self, reservations):
        """
        reservations: a list of dictionaries, each with these keys:
          - "Start Date & Time"
          - "End Date & Time"
          - "Flight Number"
          - "Customer Name"
          - "Booking Code"
          - "Car Class"
          - "Insurance"

        We'll create one page per reservation.
        """
        # Debug: show how many reservations we received
        print(f"DEBUG: PDFGenerator received {len(reservations)} reservations.")
        for i, reservation in enumerate(reservations, start=1):
            print(f"DEBUG: Reservation #{i}: {reservation}")
            self.pdf.add_page()
            self.add_reservation(reservation)

        self.pdf.output(self.filename)
        print(f"✅ PDF generated: {self.filename}")

    def add_reservation(self, reservation):
        """
        Lay out the reservation with:
          1) Start Time (no label)
          2) End Time (no label)
          3) Flight Number (with label)
          4) Customer Name (bold, underlined, bigger, 1 line above/below)
          5) The rest: Booking Code, Car Class, Insurance
        """

        # 1) Start time
        start_time = reservation.get("Start Date & Time", "")
        self.pdf.set_font("Arial", "", self.base_font_size)
        self.pdf.multi_cell(0, self.line_height, start_time)
        self.pdf.ln(3)  # small spacing

        # 2) End time
        end_time = reservation.get("End Date & Time", "")
        self.pdf.multi_cell(0, self.line_height, end_time)
        self.pdf.ln(5)  # bigger gap

        # 3) Flight Number
        flight_number = reservation.get("Flight Number", "Not Found")
        self.pdf.set_font("Arial", "B", self.base_font_size)
        self.pdf.multi_cell(0, self.line_height, f"Flight Number: {flight_number}")
        self.pdf.ln(5)

        # 4) Customer Name (big + bold + underline)
        customer_name = reservation.get("Customer Name", "Not Found")

        # One line space above
        self.pdf.ln(50)

        # Name in bold + underline + bigger
        # "BU" => Bold + Underline in FPDF syntax
        self.pdf.set_font("Arial", "BU", self.name_font_size)
        self.pdf.multi_cell(0, self.big_line_height, customer_name)

        # One line space below
        self.pdf.ln(50)

        # 5) The rest
        self.pdf.set_font("Arial", "", self.base_font_size)

        # Booking Code
        bc = reservation.get("Booking Code", "Not Found")
        self.pdf.multi_cell(0, self.line_height, f"Booking Code: {bc}")
        self.pdf.ln(3)

        # Car Class
        car_class = reservation.get("Car Class", "Not Found")
        self.pdf.multi_cell(0, self.line_height, f"Car Class: {car_class}")
        self.pdf.ln(3)

        # Insurance
        insurance = reservation.get("Insurance", "Not Found")
        self.pdf.multi_cell(0, self.line_height, f"Insurance: {insurance}")
        self.pdf.ln(5)  # extra space at end


# Example usage / test
def main():
    # A dummy list of "new reservations" for demonstration:
    dummy_reservations = [
        {
            "Start Date & Time": "24 Mar 2025, 14.00",
            "End Date & Time": "04 Apr 2025, 14.00",
            "Flight Number": "1826",
            "Customer Name": "Marc Broten",
            "Booking Code": "AW149866970",
            "Car Class": "DDMR",
            "Insurance": "Not Found"
        },
        {
            "Start Date & Time": "Mar 19, 2025 10:30",
            "End Date & Time": "Mar 25, 2025 10:30",
            "Flight Number": "Drop",
            "Customer Name": "MICHELLETO GILL",
            "Booking Code": "925-5306-NU",
            "Car Class": "ICAR",
            "Insurance": "Not Included"
        },
    ]

    # If you omit filename, it will produce something like:
    # "carvenience_report_20250314_153012.pdf"
    pdf_gen = PDFGenerator()  # you could also do PDFGenerator("my_report.pdf")
    pdf_gen.create_report(dummy_reservations)


if __name__ == "__main__":
    main()
