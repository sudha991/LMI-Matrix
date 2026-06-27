import pdfplumber
import os
import re

def extract_from_pdf(file_path):
    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    # Extract fields (customize this)
    name = re.search(r"Name[:\-]\s*(.*)", text)
    date = re.search(r"Date[:\-]\s*(.*)", text)
    amount = re.search(r"Amount[:\-]\s*(\d+)", text)

    return {
        "file": os.path.basename(file_path),
        "name": name.group(1) if name else None,
        "date": date.group(1) if date else None,
        "amount": amount.group(1) if amount else None
    }