# format_data.py

def format_all_reservations(list_of_res_data):
    """
    Takes the raw list of reservation dicts from fetch_unread_emails().
    Returns a list of standardized dicts with these keys:
      "Booking Code",
      "Customer Name",
      "Start Date & Time",
      "End Date & Time",
      "Car Class",
      "Insurance",
      "Flight Number"
    """
    formatted = []
    for data in list_of_res_data:
        formatted.append({
            "Booking Code": data.get("Booking Code", "Not Found"),
            "Customer Name": data.get("Customer Name", "Not Found"),
            "Start Date & Time": data.get("Start Date & Time", "Not Found"),
            "End Date & Time": data.get("End Date & Time", "Not Found"),
            "Car Class": data.get("Car Class", "Not Found"),
            "Insurance": data.get("Insurance", "Not Found"),
            "Flight Number": data.get("Flight Number", "Not Found")
        })
    return formatted
