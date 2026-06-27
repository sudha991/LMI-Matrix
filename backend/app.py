from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import pdfplumber
import os
import re
import pyodbc

from db import conn, cursor

# LOGIN
from login import login_bp, token_required

app = Flask(__name__)
CORS(app)

# REGISTER LOGIN
app.register_blueprint(login_bp)

PDF_FOLDER = "pdfs"

# =========================
# PROTECTED API EXAMPLE
# =========================
# =========================
# UPDATE HEADER API
# =========================
@app.route('/update-header', methods=['POST'])
@token_required
def update_header():

    data = request.json

    # 🔒 ADMIN ONLY
    if request.user['role'] != 'ADMIN':
        return jsonify({"message": "Unauthorized"}), 403

    file_name = data.get('file_name')
    revision = data.get('revision')
    date = data.get('date')
    custodian = data.get('custodian')

    try:

        # CHECK EXISTING
        cursor.execute("""
            SELECT COUNT(*)
            FROM lmi_manual
            WHERE file_name = ?
        """, (file_name,))

        exists = cursor.fetchone()[0]

        if exists > 0:

            cursor.execute("""
                UPDATE lmi_manual
                SET
                    manual_revision = ?,
                    manual_date = ?,
                    manual_custodian = ?
                WHERE file_name = ?
            """, (
                revision,
                date,
                custodian,
                file_name
            ))

        else:

            cursor.execute("""
                INSERT INTO lmi_manual
                (
                    file_name,
                    manual_revision,
                    manual_date,
                    manual_custodian
                )
                VALUES (?, ?, ?, ?)
            """, (
                file_name,
                revision,
                date,
                custodian
            ))

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Saved successfully"
        })

    except Exception as e:
        print("UPDATE ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


from db import conn, cursor



PDF_FOLDER = "pdfs"

# =========================
# CLEAN
# =========================
def clean(text):
    return re.sub(r"\s+", " ", str(text)).strip()

# =========================
# COVER PAGE EXTRACTION
# =========================
def extract_cover_page(text):

    text = text.upper()
    text = re.sub(r"\s+", " ", text)

    doc = ""
    issue = ""
    rev = ""
    date = ""

    m = re.search(r"LMI\/[A-Z0-9\/\-]+", text)
    if m:
        doc = m.group(0)

    m = re.search(r"ISSUE\s*(NO\.?)?\s*[:\-]?\s*(\d+)", text)
    if m:
        issue = m.group(2)

    m = re.search(r"(REV|REVISION)\s*(NO\.?)?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)", text)
    if m:
        rev = m.group(3)

    date_patterns = [
    # DATE: AUGUST 2023 / JULY 22
    r"DATE\s*[:\-]?\s*([A-Z]+\s*[,']?\s*\d{2,4})",

    # Standalone: AUGUST 2023 / JULY 22 / FEB.2021
    r"\b((?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\.?\s*[,']?\s*\d{2,4})\b",

    # dd.mm.yyyy
    r"\b(\d{2}\.\d{2}\.\d{4})\b"
    ]

    for p in date_patterns:
        m = re.search(p, text)
        if m:
            date = m.group(1)
            break

    return doc, issue, rev, date

# =========================
# DOC TYPE
# =========================
def extract_doc_type(doc):
    parts = doc.split("/")
    return parts[1] if len(parts) >= 2 else ""


def normalize_text(text):
    text = text.upper()

    # remove line breaks and extra spaces
    text = re.sub(r"\s+", " ", text)

    # remove spaces around slashes
    text = re.sub(r"\s*/\s*", "/", text)

    return text
#=========================
# Doc No 
#=========================
def extract_tc_doc_no(text):
    text = normalize_text(text)

    # ✅ Flexible pattern (handles all cases)
    pattern = r'LMI(?:/[A-Z0-9]+)*?/(OGN|OD|OIN)(?:/[A-Z0-9]+)*?/\d{2,4}'

    match = re.search(pattern, text)

    if match:
        return match.group()

    return ""
#=========================
# Doc Type 
#=========================
def extract_doc_type(tc_doc_no):
    if not tc_doc_no:
        return ""

    parts = tc_doc_no.split('/')

    for p in parts:
        if p in ["OGN", "OD", "OIN"]:
            return p

    return ""
# =========================
# CUSTODIAN
# =========================
def extract_custodian(text):
    for line in text.split("\n")[:25]:
        if "department" in line.lower():
            line = line.split("SIMHADRI")[0]
            line = re.sub(r"Department", "", line, flags=re.I)
            return clean(line)
    return ""

# =========================
# CLAUSE
# =========================
def extract_clauses_with_text(lines):

    clauses = []
    current_clause = ""
    buffer = []

    for line in lines:

        if re.search(r"\d{2}[./-]\d{2}[./-]\d{2,4}", line):
            continue

        if re.search(r"\b(19|20)\d{2}\b", line):
            continue

        m = re.match(r"^\s*(\d+\.\d+(?:\.\d+)?)\b", line)

        if m:
            if current_clause:
                clauses.append({
                    "clause": current_clause,
                    "text": " ".join(buffer)
                })

            current_clause = m.group(1)
            buffer = [line]

        else:
            if current_clause:
                buffer.append(line)

    if current_clause:
        clauses.append({
            "clause": current_clause,
            "text": " ".join(buffer)
        })

    return clauses
# =========================
# RESPONSIBILITY
# =========================
def extract_responsibility(line):

    line = line.upper()

    if re.search(r"\bALL\s*(DEPT|DEPTS|DEPARTMENTS?)\b", line):
        if not re.search(r"O\s*&\s*M|OPERATION", line):
            return ["ALL"]

    VALID_DEPTS = [
        "BMD","MM","OPERATION","CHEM","EEMG","EMD","EM","EMG","HR",
        "FQA","MTP","TMD","PP","SAFETY","IT","AHP","CHP","CIVIL",
        "RM","RF","C&I","AHD","AHM","AU","CFST","TS","UCE","SCE"
    ]

    mapping = {
        "MECH": "BMD",
        "MAINT": "BMD",
        "MAINTENANCE": "MM",
        "BMD": "BMD",

        "MM": "MM",
        "RM": "RM",
        "RF": "RF",
        "PP": "PP",

        "OPERATION": "OPERATION",
        "OPRN": "OPERATION",
        "OPN": "OPERATION",
        "OPS": "OPERATION",
        "O": "OPERATION",

        "CHEM": "CHEM",
        "CHEMISTRY": "CHEM",

        "EEMG": "EEMG",
        "EMD": "EMD",
        "EMG": "EMG",
        "EM": "EMD",

        "FQA": "FQA",
        "MTP": "MTP",
        "TMD": "TMD",
        "SAFETY": "SAFETY",
        "IT": "IT",
        "UCE": "UCE",
        "SCE": "SCE",
        "HR": "HR",

        "AHP": "AHM",
        "CHP": "CHP",
        "CIVIL": "CIVIL",

        "C&I": "C&I",
        "CI": "C&I",

        "AHD": "AHD",
        "AHM": "AHM",
        "AU": "AU",
        "TS": "TS",
        "CFST": "CFST"
    }

    # =========================
    # 🔥 CLEANING (IMPORTANT FIX)
    # =========================

    content = line

    # remove "Responsibility:"
    content = re.sub(r"(RESPONSIB(?:ILITY|ILITIES|LE)|RESP\.?)\s*[:\-\–—]*", "", content)

    # 🔥 merge line-break style text
    content = content.replace("\n", " ")

    # 🔥 remove noise words
    content = re.sub(
        r"\b(HOD|HOS|HEAD\s*OF|AGM|GM|DGM|DY\.?|DEPT|DEPTS|DEPARTMENTS?)\b",
        "",
        content
    )

    # 🔥 normalize separators
    content = content.replace("&", "/")
    content = content.replace("AND", "/")
    content = content.replace("-", "/")
    content = re.sub(r"\bC\s*&\s*I\b", "C_AND_I", content, flags=re.I)
    content = re.sub(r"\bO\s*&\s*M\b", "O_AND_M", content, flags=re.I)

    # 🔥 remove extra spaces
    content = re.sub(r"\s+", " ", content).strip()

    # =========================
    # 🔥 SPLIT
    # =========================
    tokens = re.split(r"/|,|\(|\)|\.", content)

    clean_tokens = []

    for t in tokens:
        t = t.strip().upper()

        # ✅ Restore C&I
        if t == "C_AND_I":
            t = "C&I"
        if t == "O_AND_M":
            t = "O&M"
        if not t or len(t) < 2:
            continue

        clean_tokens.append(t)

    # =========================
    # 🔥 MAP
    # =========================
    final = []

    for t in clean_tokens:

        # direct match
        if t in VALID_DEPTS:
            final.append(t)
            continue

        # handle combined (e.g., OPERATION SAFETY)
        words = t.split()

        for w in words:
            if w in VALID_DEPTS:
                final.append(w)

        # mapping
        for key, value in mapping.items():
            if re.fullmatch(rf"{re.escape(key)}", t):
                if value in VALID_DEPTS:
                    final.append(value)

    return list(set(final))
# =========================
# INSERT INTO DB
# =========================
def insert_data(file, doc_type, doc, custodian, rev, date, dept, clause, page, text):
    cursor.execute("""
        INSERT INTO lmi_clauses
        (file_name, doc_type, tc_doc_no, custodian, revision, date, department, clause, page, clause_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, file, doc_type, doc, custodian, rev, date, dept, clause, page, text)

# =========================
# PROCESS SINGLE PDF
# =========================
def derive_dept_from_lmi(tc_doc_no):
    if not tc_doc_no:
        return []

    parts = tc_doc_no.split("/")

    dept_map = {
        "MECH": "BMD",
        "ELEC": "EMD",
        "ELECT": "EMD",
        "ELE": "EMD",
        "SYST": "C&I",
        "INST": "C&I",
        "CHEM": "CHEM",
        "CIVIL": "CIVIL"
    }

    results = []

    for p in parts:
        p = p.upper()
        if p in dept_map:
            results.append(dept_map[p])

    return list(set(results))
# =========================
# PROCESS SINGLE PDF
# =========================
def process_single_pdf(file):

    path = os.path.join(PDF_FOLDER, file)

    try:
        with pdfplumber.open(path) as pdf:

            # =========================
            # HEADER EXTRACTION
            # =========================
            first_page = pdf.pages[0].extract_text() or ""

            doc, issue, rev, date = extract_cover_page(first_page)
            custodian = extract_custodian(first_page)
            tc_doc_no = extract_tc_doc_no(first_page)
            doc_type = extract_doc_type(tc_doc_no)

            #tc_doc_no = extract_tc_doc_no(first_page)

            # 🔥 fallback: search entire PDF if not found
            if not tc_doc_no:
                for p in pdf.pages:
                    txt = p.extract_text() or ""
                    tc_doc_no = extract_tc_doc_no(txt)
                    if tc_doc_no:
                        break
            # =========================
            # ALL DEPARTMENTS
            # =========================
            ALL_DEPTS = [
                "BMD","MM","OPERATION","CHEM","EEMG","EMD","EMG",
                "FQA","MTP","TMD","PP","SAFETY","IT","AHP","CHP","CIVIL",
                "RM","RF","C&I","AHD","AHM","AU","CFST","TS","UCE"
            ]

            last_clause = ""
            last_text = ""
            seen = set()  # 🔥 Prevent duplicates

            # =========================
            # LOOP THROUGH PAGES
            # =========================
            for page_num, page in enumerate(pdf.pages, start=1):

                text = page.extract_text() or ""
                lines = text.split("\n")

                # =========================
                # CLAUSE EXTRACTION
                # =========================
                clause_blocks = extract_clauses_with_text(lines)
                clause_map = {c["clause"]: c["text"] for c in clause_blocks}
                # =========================================================
                # 🔥🔥🔥 NEW: TABLE RESPONSIBILITY EXTRACTION 🔥🔥🔥
                # =========================================================
                tables = page.extract_tables()

                for table in tables:

                    if not table or len(table) < 2:
                        continue

                    headers = [str(h).upper() if h else "" for h in table[0]]

                    # Find Responsibility column
                    resp_index = -1
                    for i, h in enumerate(headers):
                        if "RESPONSIB" in h:
                            resp_index = i
                            break

                    if resp_index == -1:
                        continue

                    # Optional: find SI No column for clause
                    si_index = -1
                    for i, h in enumerate(headers):
                        if "SI" in h.upper():
                            si_index = i
                            break

                    for row in table[1:]:

                        if not row or len(row) <= resp_index:
                            continue

                        resp_text = str(row[resp_index] or "").strip()

                        # 🔥 FIX: merge broken lines inside table cell
                        resp_text = resp_text.replace("\n", " ")

                        # 🔥 normalize
                        resp_text = re.sub(r"\s+", " ", resp_text)

                        if not resp_text:
                            continue

                        # 🔥 If no clause, use SI No
                        if not last_clause and si_index != -1 and len(row) > si_index:
                            last_clause = str(row[si_index])

                        depts = extract_responsibility(resp_text)

                        for d in depts:

                            target_depts = ALL_DEPTS if d == "ALL" else [d]

                            for dept in target_depts:

                                if not last_clause:
                                    continue

                                key = (file, dept, last_clause, page_num)

                                if key in seen:
                                    continue

                                seen.add(key)

                                insert_data(
                                    file,
                                    doc_type,
                                    tc_doc_no,
                                    custodian,
                                    rev,
                                    date,
                                    dept,
                                    last_clause,
                                    page_num,
                                    last_text[:500]
                                )
                # =========================
                # LINE BY LINE PROCESSING
                # =========================
                for i, line in enumerate(lines):

                    line = line.strip()
                    if not line:
                        continue
                    # 🔥 merge next line if broken
                    if line.endswith("/") or "HEAD OF" in line.upper():
                        if i + 1 < len(lines):
                            line = line + " " + lines[i + 1].strip()        
                    # -------------------------
                    # CLAUSE DETECTION (KEEP THIS SAME)
                    # -------------------------
                    clause_match = re.match(r"^\s*(\d+\.\d+(?:\.\d+)?)\b", line)

                    if clause_match:
                        last_clause = clause_match.group(1)
                        last_text = clause_map.get(last_clause, "")

                    # -------------------------
                    # 🔥 NEW RESPONSIBILITY DETECTION
                    # -------------------------
                    if re.search(r"\b(responsib(?:ility|ilities|le)|resp\.?)\b", line, re.I):

                        content = ""

                        # case 1: same line
                        m = re.search(
                            r"(responsib(?:ility|ilities|le)|resp\.?)\s*[:\-\–—()]*\s*(.*)",
                            line,
                            re.I
                        )

                        if m and m.group(2).strip():
                            content = m.group(2)

                        # 🔥 case 2: next line
                        else:
                            if i + 1 < len(lines):
                                content = lines[i + 1].strip()

                        if not content:
                            continue

                        # 🔥 normalize (VERY IMPORTANT)
                        content = content.upper()
                        content = content.replace("-", "/")
                        content = content.replace("&", "/")
                        content = content.replace("AND", "/")
                        content = re.sub(r"\bDEPTS?\b\.?", "", content)

                        # -------------------------
                        # EXTRACT DEPARTMENTS
                        # -------------------------
                        depts = extract_responsibility(content)

                        if not depts:
                            continue

                        # -------------------------
                        # INSERT INTO DB (KEEP SAME)
                        # -------------------------
                        for d in depts:

                            target_depts = ALL_DEPTS if d == "ALL" else [d]

                            for dept in target_depts:

                                if not last_clause:
                                    continue

                                key = (file, dept, last_clause, page_num)

                                if key in seen:
                                    continue

                                seen.add(key)

                                insert_data(
                                    file,
                                    doc_type,
                                    tc_doc_no,
                                    custodian,
                                    rev,
                                    date,
                                    dept,
                                    last_clause,
                                    page_num,
                                    last_text[:500]
                                )

            # =========================
            # 🔥 FALLBACK: NO RESPONSIBILITY FOUND
            # =========================
            if len(seen) == 0:

                fallback_depts = derive_dept_from_lmi(tc_doc_no)

                # if still empty → insert at least 1 row
                if not fallback_depts:
                    fallback_depts = ["NO_DATA"]

                for dept in fallback_depts:
                    insert_data(
                        file,
                        doc_type,
                        tc_doc_no,
                        custodian,
                        rev,
                        date,
                        dept,
                        "",   # no clause
                        0,
                        "No Responsibility Found"
                    )

    except Exception as e:
        print("ERROR:", file, e)

# =========================
# PROCESS API
# =========================
@app.route("/process")
def process():

    files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

    cursor.execute("DELETE FROM lmi_clauses")

    for f in files:
        process_single_pdf(f)

    conn.commit()

    return jsonify({"status": "done", "processed": len(files)})

# =========================
# DATA API (CLICKABLE FORMAT)
# =========================
@app.route("/data")
def data():

    # 🔥 Get all PDF files from folder
    all_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

    cursor.execute("""
        SELECT 
            lc.file_name,
            lc.doc_type,
            lc.tc_doc_no,

            -- 🔥 PRIORITY: manual > extracted
            ISNULL(lm.manual_custodian, lc.custodian) AS custodian,
            ISNULL(lm.manual_revision, lc.revision) AS revision,
            ISNULL(lm.manual_date, lc.date) AS date,

            lc.department,
            lc.clause,
            lc.page,
            lc.clause_text
        FROM lmi_clauses lc
        LEFT JOIN lmi_manual lm 
            ON lc.file_name = lm.file_name
                   
    """)

    rows = cursor.fetchall()

    grouped = {}

    # 🔥 Initialize ALL files first (IMPORTANT)
    for f in all_files:
        grouped[f] = {
            "FILE NAME": f,
            "DOC TYPE": "",
            "TC DOC NO": "",
            "CUSTODIAN DEPT": "",
            "REVISION": "",
            "DATE": ""
        }

    # 🔥 Fill data from DB
    for r in rows:

        key = r.file_name

        if key not in grouped:
            grouped[key] = {
                "FILE NAME": key,
                "DOC TYPE": "",
                "TC DOC NO": "",
                "CUSTODIAN DEPT": "",
                "REVISION": "",
                "DATE": ""
            }

        grouped[key].update({
            "FILE NAME": r.file_name,
            "DOC TYPE": r.doc_type,
            "TC DOC NO": r.tc_doc_no,
            "CUSTODIAN DEPT": r.custodian,
            "REVISION": r.revision,
            "DATE": r.date
        })

        dept = r.department if r.department else "NO_DATA"
        invalid_keys = ["FILE NAME", "DOC TYPE", "TC DOC NO", "CUSTODIAN DEPT", "REVISION", "DATE"]

        if dept in invalid_keys:
            dept = "OTHER"
        value = {
            "clause": r.clause,
            "page": r.page,
            "file": r.file_name,
            "text": getattr(r, "clause_text", "")
        }

        if dept not in grouped[key] or not isinstance(grouped[key].get(dept), list):
            grouped[key][dept] = []

        grouped[key][dept].append(value)

    return jsonify({"data": list(grouped.values())})
# =========================
# SERVE PDF
# =========================
@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)