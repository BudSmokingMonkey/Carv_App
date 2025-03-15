import imaplib
import email
import re
import os
from email.header import decode_header
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

# Print environment variables for debugging
print("GMAIL_EMAIL:", os.getenv("GMAIL_EMAIL"))
print("GMAIL_APP_PASSWORD:", os.getenv("GMAIL_APP_PASSWORD"))

EMAIL_USER = os.getenv("GMAIL_EMAIL")
EMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

if not EMAIL_USER or not EMAIL_PASS:
    raise ValueError("GMAIL_EMAIL or GMAIL_APP_PASSWORD environment variables are not set.")

def connect_to_email():
    """Connect to Gmail via IMAP."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        return mail
    except Exception as e:
        print("Error connecting to email:", e)
        return None

def clean_html(raw_html):
    """Convert HTML email body to plain text, removing scripts and styles."""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ").strip()
    text = text.replace("\xa0", " ")
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r':\s+', ': ', text)
    return text.strip()

def extract_body_text(msg):
    """Extract text from a multi-part email for text-based logic."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition") or "").lower()
            if ctype in ["text/plain", "text/html"] and "attachment" not in cdisp:
                try:
                    body = part.get_payload(decode=True)
                    if body:
                        return body.decode("utf-8", errors="ignore")
                except Exception as e:
                    print("Error decoding body:", e)
                    return ""
        return ""
    else:
        try:
            body = msg.get_payload(decode=True)
            if body:
                return body.decode("utf-8", errors="ignore")
        except Exception as e:
            print("Error decoding body:", e)
        return ""
    return ""

############################
# Broker-Specific Parse Functions
############################

def parse_cartrawler(text):
    details = {}
    text = clean_html(text)
    bc = re.search(r"Ref\s*no:\s*([\w\d]+)", text, re.IGNORECASE)
    details["Booking Code"] = bc.group(1) if bc else "Not Found"
    cust = re.search(r"Customer\s*name:\s*([A-Za-z\s]+)(?=\s*Customer\s*phone)", text, re.IGNORECASE)
    details["Customer Name"] = cust.group(1).strip() if cust else "Not Found"
    st = re.search(r"Pick\s*up\s*date\s*&\s*time\s*:\s*([\d]{2}\s*\w{3}\s*\d{4},\s*\d{2}\.\d{2})", text, re.IGNORECASE)
    details["Start Date & Time"] = st.group(1) if st else "Not Found"
    et = re.search(r"Drop\s*off\s*date\s*&\s*time\s*:\s*([\d]{2}\s*\w{3}\s*\d{4},\s*\d{2}\.\d{2})", text, re.IGNORECASE)
    details["End Date & Time"] = et.group(1) if et else "Not Found"
    cclass = re.search(r"Group\s*Name\s*:\s*([A-Z]{4})", text, re.IGNORECASE)
    details["Car Class"] = cclass.group(1) if cclass else "Not Found"
    ins = re.search(r"Rate\s*Code:\s*(Inclusive|Exclusive|Included|Not Included)", text, re.IGNORECASE)
    if ins:
        val = ins.group(1).lower()
        details["Insurance"] = "Included" if val in ["inclusive", "included"] else "Not Included"
    else:
        details["Insurance"] = "Not Found"
    fl = re.search(r"Flight\s*No\s*:\s*(\S+)", text, re.IGNORECASE)
    details["Flight Number"] = fl.group(1) if fl else "Not Found"
    return details

def parse_nu(text):
    details = {}
    text = clean_html(text)
    bc = re.search(r"Your\s*Reservation\s*#\s*Is\s*([\w\d\-]+)", text, re.IGNORECASE)
    details["Booking Code"] = bc.group(1) if bc else "Not Found"
    cust = re.search(r"Name:\s*([\w\s]+)(?=\s*Email)", text, re.IGNORECASE)
    details["Customer Name"] = cust.group(1).strip() if cust else "Not Found"
    st = re.search(r"Pick\s*UP\s*([\w]{3}\s*\d{1,2},\s*\d{4}\s*\d{1,2}:\d{2})", text, re.IGNORECASE)
    details["Start Date & Time"] = st.group(1) if st else "Not Found"
    et = re.search(r"Drop\s*OFF\s*([\w]{3}\s*\d{1,2},\s*\d{4}\s*\d{1,2}:\d{2})", text, re.IGNORECASE)
    details["End Date & Time"] = et.group(1) if et else "Not Found"
    cclass = re.search(r"Vehicle\s*Class\s*([A-Z]{4})", text, re.IGNORECASE)
    details["Car Class"] = cclass.group(1) if cclass else "Not Found"
    details["Insurance"] = "Included" if "Inclusive" in text else "Not Included"
    fl = re.search(r"Flight:\s*([\w\d\-]+)", text, re.IGNORECASE)
    details["Flight Number"] = fl.group(1) if fl else "Not Found"
    return details

def parse_booking_group(text):
    details = {}
    text = clean_html(text)
    bc = re.search(r"Our\s*Ref:\s*([\w\-]+)", text, re.IGNORECASE)
    details["Booking Code"] = bc.group(1) if bc else "Not Found"
    cust = re.search(r"Customer:\s*([\w\s]+)(?=\s*Pick Up)", text, re.IGNORECASE)
    details["Customer Name"] = cust.group(1).strip() if cust else "Not Found"
    st = re.search(r"Pick\s*Up\s*Date:\s*(\d{2}\s*\w{3}\s*\d{4},\s*\d{2}:\d{2})", text, re.IGNORECASE)
    details["Start Date & Time"] = st.group(1) if st else "Not Found"
    et = re.search(r"Drop\s*Off\s*Date:\s*(\d{2}\s*\w{3}\s*\d{4},\s*\d{2}:\d{2})", text, re.IGNORECASE)
    details["End Date & Time"] = et.group(1) if et else "Not Found"
    cclass = re.search(r"Car\s*Group:\s*([A-Z]{4})", text, re.IGNORECASE)
    details["Car Class"] = cclass.group(1) if cclass else "Not Found"
    rc = re.search(r"Rate\s*Code:\s*(Exclusive|Inclusive)", text, re.IGNORECASE)
    if rc:
        val = rc.group(1).lower()
        details["Insurance"] = "Included" if val == "inclusive" else "Not Included"
    else:
        details["Insurance"] = "Not Found"
    fl = re.search(r"Flight\s*No\s*:\s*(\S+)", text, re.IGNORECASE)
    details["Flight Number"] = fl.group(1) if fl else "Not Found"
    return details

def parse_rentalcars(text):
    details = {}
    text = clean_html(text)
    bc = re.search(r"RC\s*booking\s*ref:\s*(\d+)", text, re.IGNORECASE)
    details["Booking Code"] = bc.group(1) if bc else "Not Found"
    cust = re.search(r"Customer\s*name:\s*([\w\s]+)", text, re.IGNORECASE)
    details["Customer Name"] = cust.group(1).strip() if cust else "Not Found"
    st = re.search(r"Pick\s*up\s*date:\s*(\d{2}\s*\d{2}\s*\d{4}\s*\d{2}:\d{2})", text, re.IGNORECASE)
    details["Start Date & Time"] = st.group(1) if st else "Not Found"
    et = re.search(r"Drop\s*off\s*date:\s*(\d{2}\s*\d{2}\s*\d{4}\s*\d{2}:\d{2})", text, re.IGNORECASE)
    details["End Date & Time"] = et.group(1) if et else "Not Found"
    cclass = re.search(r"Class\s*of\s*car\s*booked:\s*([A-Z]{4})", text, re.IGNORECASE)
    details["Car Class"] = cclass.group(1) if cclass else "Not Found"
    details["Insurance"] = "Included"
    fl = re.search(r"Flight\s*No\s*:\s*(\S+)", text, re.IGNORECASE)
    details["Flight Number"] = fl.group(1) if fl else "Not Found"
    return details

def parse_text_broker(msg, subject):
    body = extract_body_text(msg)
    if not body:
        return {}
    
    # Check if it's a web inquiry by presence of "Dear" and a known car brand:
    if "dear" in body.lower() and any(b in body.lower() for b in ["hyundai", "dodge", "nissan", "toyota", "ford"]):
        return parse_web_inquiry(body)
    
    if "ct reference" in subject.lower():
        return parse_cartrawler(body)
    elif "nu car rentals reservation" in subject.lower():
        return parse_nu(body)
    elif "booking group" in subject.lower():
        return parse_booking_group(body)
    elif "reservation was created" in subject.lower():
        return parse_rentalcars(body)
    else:
        return {}

############################
# Sunny Cars PDF Parser
############################
def find_pdf_attachment(msg):
    """
    Recursively search for a PDF attachment in the message or nested forwarded messages.
    Returns the first PDF attachment found, or None if not found.
    """
    for part in msg.walk():
        content_type = part.get_content_type()
        disp = str(part.get("Content-Disposition") or "").lower()
        fname = part.get_filename()
        if fname and fname.lower().endswith(".pdf") and "attachment" in disp:
            return part
    for part in msg.walk():
        if part.get_content_type() == "message/rfc822":
            nested_payload = part.get_payload()
            if isinstance(nested_payload, list):
                for nested_msg in nested_payload:
                    pdf_part = find_pdf_attachment(nested_msg)
                    if pdf_part:
                        return pdf_part
            else:
                pdf_part = find_pdf_attachment(nested_payload)
                if pdf_part:
                    return pdf_part
    return None

def parse_sunnycars_pdf(msg):
    """
    For Sunny Cars, locate the PDF attachment (even if nested within forwarded messages),
    extract its text, and then parse the reservation details from the lower section.
    Expected fields (from your sample):
      - Booking Code: extracted from "Our Ref:" (e.g. "14113981")
      - Start Date & Time and End Date & Time: first two date/time strings in "dd.mm.yyyy / hh:mm" format
      - Car Class: extracted from the lower section after "Car Group:" by skipping common header lines (like "Comment:", "RESERVATION", "Aruba APT")
      - Customer Name: from the "Driver:" line (with common prefixes removed)
      - Insurance is assumed "Included"
      - Flight Number defaults to "Not Found"
    """
    pdf_attachment = find_pdf_attachment(msg)
    if not pdf_attachment:
        return {
            "Booking Code": "Not Found",
            "Customer Name": "Not Found",
            "Start Date & Time": "Not Found",
            "End Date & Time": "Not Found",
            "Car Class": "Not Found",
            "Insurance": "Not Found",
            "Flight Number": "Not Found"
        }
    
    file_data = pdf_attachment.get_payload(decode=True)
    if not file_data:
        return {
            "Booking Code": "Not Found",
            "Customer Name": "Not Found",
            "Start Date & Time": "Not Found",
            "End Date & Time": "Not Found",
            "Car Class": "Not Found",
            "Insurance": "Not Found",
            "Flight Number": "Not Found"
        }
    
    temp_pdf = "temp_sunnycars.pdf"
    with open(temp_pdf, "wb") as f:
        f.write(file_data)
    
    text = ""
    try:
        with open(temp_pdf, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    finally:
        os.remove(temp_pdf)
    
    print("DEBUG: Extracted PDF text (first 1000 chars):")
    print(text[:1000])
    
    # --- Parsing the lower section of the PDF ---
    # 1) Booking Code: Look for "Our Ref:" followed by numbers.
    bc_match = re.search(r"Our\s*Ref\.?:\s*(\d+)", text, re.IGNORECASE)
    booking_code = bc_match.group(1) if bc_match else "Not Found"
    
    # 2) Dates: Find all occurrences of dates in the format "dd.mm.yyyy / hh:mm".
    date_matches = re.findall(r"(\d{2}\.\d{2}\.\d{4}\s*/\s*\d{2}:\d{2})", text)
    if len(date_matches) >= 2:
        start_dt = date_matches[0]
        end_dt = date_matches[1]
    else:
        start_dt = "Not Found"
        end_dt = "Not Found"
    
    # 3) Car Class: Split on "Car Group:" and then skip header lines.
    car_group_section = re.split(r"Car\s*Group:\s*", text, flags=re.IGNORECASE)
    if len(car_group_section) > 1:
        # Split the remainder into lines
        lines = [line.strip() for line in car_group_section[1].splitlines() if line.strip()]
        # Define words to skip (in uppercase for comparison)
        skip_words = {"COMMENT:", "RESERVATION", "ARUBA APT"}
        car_class = "Not Found"
        for line in lines:
            # Compare in uppercase
            if line.upper() not in skip_words:
                car_class = line
                break
    else:
        car_class = "Not Found"
    
    # 4) Customer Name: Extract from the "Driver:" line.
    driver_match = re.search(r"Driver:\s*(.*)", text, re.IGNORECASE)
    if driver_match:
        driver_line = driver_match.group(1).strip()
        # Remove common prefixes like "Mr.", "Mrs.", or "Ms."
        driver_line = re.sub(r"^(Mr\.|Mrs\.|Ms\.)\s*", "", driver_line, flags=re.IGNORECASE)
        customer_name = driver_line
    else:
        customer_name = "Not Found"
    
    details = {
        "Booking Code": booking_code,
        "Customer Name": customer_name,
        "Start Date & Time": start_dt,
        "End Date & Time": end_dt,
        "Car Class": car_class,
        "Insurance": "Included",    # Assume Sunny Cars always include insurance
        "Flight Number": "Not Found"
    }
    return details


############################
# Web Inquiry Parser
############################
import re

import re

import re

import re

def parse_web_inquiry(text, debug=True):
    """
    Parse a free-form web reservation inquiry email.
    
    Extracts:
      - Customer Name: from the greeting ("Dear <Name>,")
      - Car Class: detected as car brand and model (e.g., "Hyundai Accent")
      - Start Date & Time: from a date range like "March 9-15" (start date: "March 9")
      - End Date & Time: from the same pattern (end date: "March 15")
      - Booking Number: uses the cost as a surrogate (e.g., "$358.85")
      - Insurance: if "Collision Damage Waiver" is followed by "Optional" => "Not Included"; otherwise, "Included"
      - Flight Number: defaults to "Not Found"
    """
    details = {
        "Customer Name": "Not Found",
        "Car Class": "Not Found",
        "Start Date & Time": "Not Found",
        "End Date & Time": "Not Found",
        "Booking Number": "Not Found",
        "Insurance": "Not Found",
        "Flight Number": "Not Found"
    }
    
    if debug:
        print("DEBUG: Original text:")
        print(text)
    
    # Check if the input text is empty
    if not text.strip():
        if debug:
            print("DEBUG: The input text is empty after stripping whitespace.")
        return details
    
    # Normalize whitespace (collapse multiple spaces/newlines into a single space)
    normalized_text = " ".join(text.split())
    if debug:
        print("DEBUG: Normalized text:")
        print(normalized_text)
    
    # 1. Extract Customer Name from greeting (e.g., "Dear Tirso,")
    cust_match = re.search(r"(Dear|Hi|Hello)[\s,]+([^\s,]+)", normalized_text, re.IGNORECASE)
    if debug:
        print("DEBUG: Customer Name regex match:", cust_match)
    if cust_match:
        details["Customer Name"] = cust_match.group(2).strip()
        if debug:
            print("DEBUG: Extracted Customer Name:", details["Customer Name"])
    
    # 2. Extract Car Class: known brands followed by a model (e.g., "Hyundai Accent")
    car_match = re.search(r"(Hyundai|Dodge|Nissan|Toyota|Ford)\s+([A-Za-z0-9]+)", normalized_text, re.IGNORECASE)
    if debug:
        print("DEBUG: Car Class regex match:", car_match)
    if car_match:
        brand = car_match.group(1).strip().title()
        model = car_match.group(2).strip().title()
        details["Car Class"] = f"{brand} {model}"
        if debug:
            print("DEBUG: Extracted Car Class:", details["Car Class"])
    
    # 3. Extract Dates from a pattern like "March 9-15"
    date_match = re.search(r"([A-Za-z]+)\s+(\d+)\s*-\s*(\d+)", normalized_text)
    if debug:
        print("DEBUG: Date regex match:", date_match)
    if date_match:
        month = date_match.group(1).strip()
        day_start = date_match.group(2).strip()
        day_end = date_match.group(3).strip()
        details["Start Date & Time"] = f"{month} {day_start}"
        details["End Date & Time"] = f"{month} {day_end}"
        if debug:
            print("DEBUG: Extracted Start Date:", details["Start Date & Time"])
            print("DEBUG: Extracted End Date:", details["End Date & Time"])
    
    # 4. Extract Booking Number using the cost as a surrogate (e.g., "cost US $ 358.85")
    cost_match = re.search(r"cost\s+US\s*\$\s*([\d\.]+)", normalized_text, re.IGNORECASE)
    if debug:
        print("DEBUG: Cost regex match:", cost_match)
    if cost_match:
        details["Booking Number"] = f"${cost_match.group(1)}"
        if debug:
            print("DEBUG: Extracted Booking Number (Cost):", details["Booking Number"])
    
    # 5. Extract Insurance: check for "Collision Damage Waiver" and if it's followed by "Optional"
    insurance_match = re.search(r"Collision\s*Damage\s*Waiver\s*[:,]?\s*(Optional)?", normalized_text, re.IGNORECASE)
    if debug:
        print("DEBUG: Insurance regex match:", insurance_match)
    if insurance_match:
        # If "Optional" is captured, then insurance is not included; otherwise, included.
        if insurance_match.group(1) and insurance_match.group(1).lower() == "optional":
            details["Insurance"] = "Not Included"
        else:
            details["Insurance"] = "Included"
        if debug:
            print("DEBUG: Extracted Insurance:", details["Insurance"])
    else:
        details["Insurance"] = "Not Included"
        if debug:
            print("DEBUG: 'Collision Damage Waiver' not found; defaulting Insurance to 'Not Included'")
    
    # 6. Flight Number remains default (not available in web inquiries)
    details["Flight Number"] = "Not Found"
    
    if debug:
        print("DEBUG: Final extracted details:")
        print(details)
    
    return details

# Example usage with your sample email text:
if __name__ == "__main__":
    email_text = """Dear Tirso,
    
    The Hyundai Accent, a 4-door sedan, automatic transmission with air-conditioning, March 9-15, cost US $ 358.85
    
    The rate includes all the fees, all the taxes, the damage to third party and the liability coverage, with a deductible of $ 270.- and the Collision Damage Waiver, it covers the rented vehicle in case of an accident, with a deductible of $ 648.-
    """
    result = parse_web_inquiry(email_text, debug=True)
    print("Extracted Details:", result)

############################
# Main fetch function
############################
def fetch_unread_emails():
    mail = connect_to_email()
    if not mail:
        return []
    
    all_reservations = []
    try:
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} unread emails.\n")
        
        for email_id in email_ids:
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
            except imaplib.IMAP4.abort:
                mail.store(email_id, '+FLAGS', '\\Seen')
                continue
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg_obj = email.message_from_bytes(response_part[1])
                    decoded_subj = decode_header(msg_obj["Subject"])
                    subject_parts = []
                    for sub_item, enc in decoded_subj:
                        if isinstance(sub_item, bytes):
                            subject_parts.append(sub_item.decode(enc or "utf-8", errors="ignore"))
                        else:
                            subject_parts.append(sub_item)
                    subject = "".join(subject_parts)
                    print(f"Subject: {subject}\n")
                    
                    if "sunnycars" in subject.lower():
                        details = parse_sunnycars_pdf(msg_obj)
                    else:
                        details = parse_text_broker(msg_obj, subject)
                    
                    print("📋 Extracted Reservation Details:", details, "\n")
                    all_reservations.append(details)
            
            mail.store(email_id, '+FLAGS', '\\Seen')
    finally:
        mail.logout()
    
    return all_reservations

if __name__ == "__main__":
    results = fetch_unread_emails()
    print("All reservations:\n")
    for r in results:
        print(r)
