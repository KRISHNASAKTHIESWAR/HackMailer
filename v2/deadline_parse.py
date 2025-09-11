import dateparser

def parse_deadline(deadline_str):
    if deadline_str.startswith("OCR Dates found:"):
        # When OCR fallback returns, no direct parse, handle separately or skip
        print(f"OCR fallback date candidates: {deadline_str}")
        return None
    dt = dateparser.parse(deadline_str)
    if dt:
        return dt.date()  # Return datetime.date object
    else:
        print(f"Failed to parse deadline: {deadline_str}")
        return None
